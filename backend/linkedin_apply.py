# === backend/linkedin_apply.py ===
from playwright.async_api import async_playwright
import asyncio
from google_sheets import log_job_to_sheet

async def auto_fill_common_fields(page):
    try:
        # Work Authorization
        work_auth_selectors = [
            "input[aria-label*='authorized to work']",
            "input[aria-label*='work authorization']",
            "input[aria-label*='legally authorized']",
            "label:has-text('authorized to work') input",
            "label:has-text('work authorization') input",
            "label:has-text('legally authorized') input",
            "select:has(option:has-text('authorized'))",
            "select:has(option:has-text('authorization'))"
        ]

        for selector in work_auth_selectors:
            if await page.locator(selector).count() > 0:
                element = page.locator(selector).first
                tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                if await element.get_attribute("type") == "radio":
                    await element.check()
                elif await element.is_editable():
                    await element.fill("Yes")
                elif tag_name == "select":
                    await element.select_option(label="Yes")
                break

        # Willing to relocate
        if await page.locator("input[aria-label*='willing to relocate']").count() > 0:
            await page.locator("input[aria-label*='willing to relocate']").first.check()

        # Expected salary
        if await page.locator("input[aria-label*='expected salary']").count() > 0:
            await page.locator("input[aria-label*='expected salary']").first.fill("100000")

        # Years of experience
        if await page.locator("input[aria-label*='years of experience']").count() > 0:
            await page.locator("input[aria-label*='years of experience']").first.fill("2")

        # City
        if await page.locator("input[aria-label*='city']").count() > 0:
            await page.locator("input[aria-label*='city']").first.fill("Boston")

        # Handle dropdowns only if not pre-selected or has placeholder
        dropdowns = await page.locator("select").all()
        for dropdown in dropdowns:
            try:
                current_value = await dropdown.input_value()
                selected_label = (await dropdown.locator("option:checked").text_content() or "").strip().lower()
                options = await dropdown.locator("option").all_text_contents()
                options_lower = [opt.strip().lower() for opt in options]

                if not current_value.strip() or "select" in selected_label or "option" in selected_label or selected_label == "":
                    if "yes" in options_lower:
                        await dropdown.select_option(label="Yes")
                    elif "years" in (await dropdown.get_attribute("aria-label") or "") or "experience" in (await dropdown.get_attribute("aria-label") or ""):
                        await dropdown.select_option(index=min(3, len(options)-1))
                    else:
                        await dropdown.select_option(index=1)
                else:
                    print("✅ Dropdown already filled, skipping.")
            except Exception as e:
                print(f"⚠️ Skipping dropdown due to: {e}")

        # Handle Yes/No radio button groups (if neither selected, choose Yes)
        radio_groups = await page.locator("fieldset").all()
        for group in radio_groups:
            radios = group.locator("input[type='radio']")
            labels = await group.locator("label").all_text_contents()
            if "Yes" in labels and "No" in labels:
                yes_radio = radios.nth(labels.index("Yes"))
                if not await yes_radio.is_checked():
                    await yes_radio.check()

        # Fill number fields with default values for questions about experience
        number_inputs = await page.locator("input[type='text'], input[type='number']").all()
        for input_box in number_inputs:
            placeholder = await input_box.get_attribute("placeholder") or ""
            aria_label = await input_box.get_attribute("aria-label") or ""
            value = await input_box.input_value()
            if ("year" in placeholder.lower() or "year" in aria_label.lower() or "experience" in aria_label.lower()) and not value:
                await input_box.fill("2")

    except Exception as e:
        print(f"⚠️ Failed to auto-fill fields: {e}")
        raise


async def auto_apply_linkedin_jobs(keywords, job_type):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=50)
            context = await browser.new_context(storage_state="linkedin_session.json")
            page = await context.new_page()

            location = "United States"
            jobs_applied = 0
            max_applications = 10

            for kw in keywords.split(","):
                query = kw.strip().replace(" ", "%20")
                url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location={location}&f_TPR=r86400&f_AL=true"
                try:
                    await page.goto(url)
                except Exception as nav_error:
                    print(f"❌ Failed to navigate to LinkedIn search URL: {nav_error}")
                    continue

                await asyncio.sleep(3)

                try:
                    job_cards = await page.locator(".job-card-container--clickable").all()
                except Exception as card_error:
                    print(f"❌ Failed to load job cards: {card_error}")
                    continue

                for card in job_cards:
                    if jobs_applied >= max_applications:
                        break
                    try:
                        if await page.locator(".artdeco-modal__dismiss").count() > 0:
                            await page.locator(".artdeco-modal__dismiss").first.click()
                            await asyncio.sleep(0.5)
                            if await page.locator("button:has-text('Discard')").count() > 0:
                                await page.locator("button:has-text('Discard')").click()
                                await asyncio.sleep(0.5)

                        await card.scroll_into_view_if_needed()
                        await card.click()
                        await asyncio.sleep(2)

                        title_el = page.locator(".job-details-jobs-unified-top-card__job-title h1")
                        company_el = page.locator(".job-details-jobs-unified-top-card__company-name a")

                        title = await title_el.text_content() if await title_el.count() > 0 else "Unknown"
                        company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                        job_url = page.url

                        print(f"🔍 Checking job: {title} at {company}")

                        try:
                            await page.wait_for_selector(".artdeco-button:has(span:text('Easy Apply'))", timeout=3000)
                            easy_apply_button = page.locator(".artdeco-button:has(span:text('Easy Apply'))").first

                            if await easy_apply_button.is_visible():
                                print(f"✅ Found Easy Apply for: {title} at {company}")
                                await easy_apply_button.click()
                                await asyncio.sleep(1.5)

                                try:
                                    await asyncio.wait_for(auto_fill_common_fields(page), timeout=10)

                                    while True:
                                        try:
                                            await asyncio.wait_for(auto_fill_common_fields(page), timeout=10)
                                        except Exception as fill_error:
                                            print(f"⚠️ Error during auto-fill: {fill_error}")
                                            break

                                        if await page.locator("button:has-text('Submit application')").count() > 0:
                                            break
                                        if await page.locator("button:has-text('Review')").count() > 0:
                                            await page.locator("button:has-text('Review')").click()
                                            await asyncio.sleep(1.5)
                                            break

                                        next_or_review = page.locator("button[data-easy-apply-next-button]")
                                        if await next_or_review.count() == 0:
                                            break

                                        label = await next_or_review.first.text_content()
                                        print(f"➡️ Found Easy Apply button: '{label.strip()}', clicking it")
                                        await next_or_review.first.click()
                                        await asyncio.sleep(0.8)

                                    if await page.locator("button:has-text('Submit application')").count() > 0:
                                        await page.locator("button:has-text('Submit application')").click()
                                        jobs_applied += 1
                                        log_job_to_sheet({
                                            "title": title.strip(),
                                            "company": company.strip(),
                                            "url": job_url,
                                            "platform": "LinkedIn",
                                            "status": "Applied ✅",
                                            "notes": "Application submitted successfully"
                                        })
                                    else:
                                        raise Exception("No Submit button found")

                                except Exception as app_error:
                                    print(f"⚠️ Application flow error: {app_error}")
                                    log_job_to_sheet({
                                        "title": title.strip(),
                                        "company": company.strip(),
                                        "url": job_url,
                                        "platform": "LinkedIn",
                                        "status": "Skipped ❌",
                                        "notes": f"Error during apply: {app_error}"
                                    })

                                    if await page.locator(".artdeco-modal__dismiss").count() > 0:
                                        await page.locator(".artdeco-modal__dismiss").first.click()
                                        await asyncio.sleep(0.5)
                                        discard = page.locator("button:has-text('Discard')")
                                        if await discard.count() > 0:
                                            await discard.click()

                        except Exception as e:
                            print(f"⚠️ No Easy Apply for: {title} at {company} — {e}")

                        await asyncio.sleep(1)
                    except Exception as e:
                        print(f"⚠️ Skipping job due to error: {e}")
                        continue

            await browser.close()
            return {"message": f"Auto-applied to {jobs_applied} Easy Apply jobs on LinkedIn."}

    except Exception as fatal_error:
        print(f"💥 Fatal error in auto-apply: {fatal_error}")
        return {"message": "Failed to complete LinkedIn auto-apply run."}
