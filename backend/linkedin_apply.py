# === backend/linkedin_apply.py ===
from playwright.async_api import async_playwright
import asyncio
from google_sheets import log_job_to_sheet

async def auto_fill_common_fields(page):
    try:
        # Work Authorization - More resilient with additional checks
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
            try:
                if await page.locator(selector).count() > 0:
                    element = page.locator(selector).first
                    if await element.is_visible() and await element.is_enabled():
                        tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                        input_type = await element.get_attribute("type")
                        
                        if input_type == "radio":
                            await element.check(timeout=2000)
                        elif await element.is_editable():
                            await element.fill("Yes", timeout=2000)
                        elif tag_name == "select":
                            await element.select_option(label="Yes", timeout=2000)
                        break
            except:
                continue  # Skip to next selector if any error occurs

        # Willing to relocate - More resilient
        relocate_selectors = [
            "input[aria-label*='willing to relocate']",
            "label:has-text('relocate') input[type='checkbox']",
            "label:has-text('relocate') input[type='radio']"
        ]
        
        for selector in relocate_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    element = page.locator(selector).first
                    if await element.is_visible() and await element.is_enabled():
                        await element.check(timeout=2000)
                        break
            except:
                continue

        # Expected salary - More resilient with fallbacks
        salary_selectors = [
            "input[aria-label*='expected salary']",
            "input[placeholder*='expected salary']",
            "input[name*='salary']"
        ]
        
        for selector in salary_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    element = page.locator(selector).first
                    if await element.is_visible() and await element.is_enabled():
                        await element.fill("100000", timeout=2000)
                        break
            except:
                continue

        # Years of experience - More resilient
        exp_selectors = [
            "input[aria-label*='years of experience']",
            "input[placeholder*='years of experience']",
            "input[name*='experience']"
            "label:has-text('years of work experience') input",
            "label:has-text('years of experience') input",
            "label:has-text('years with') input",
            "label:has-text('experience with') input",
            "label:has-text('how many years') input"

        ]
        
        for selector in exp_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    element = page.locator(selector).first
                    if await element.is_visible() and await element.is_enabled():
                        await element.fill("2", timeout=2000)
                        break
            except:
                continue
            

        # City field - More resilient
        city_selectors = [
            "input[aria-label*='city']",
            "input[placeholder*='city']",
            "input[name*='city']"
        ]
        
        for selector in city_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    element = page.locator(selector).first
                    if await element.is_visible() and await element.is_enabled():
                        await element.fill("Boston", timeout=2000)
                        
                        break
            except:
                continue

        # Handle dropdowns - More resilient with additional checks
        dropdowns = await page.locator("select").all()
        for dropdown in dropdowns:
            try:
                if await dropdown.is_visible() and await dropdown.is_enabled():
                    current_value = await dropdown.input_value()
                    selected_label = (await dropdown.locator("option:checked").text_content() or "").strip().lower()
                    options = await dropdown.locator("option").all_text_contents()
                    options_lower = [opt.strip().lower() for opt in options]

                    if not current_value.strip() or "select" in selected_label or "option" in selected_label or selected_label == "":
                        if "yes" in options_lower:
                            await dropdown.select_option(label="Yes", timeout=2000)
                        elif "years" in (await dropdown.get_attribute("aria-label") or "").lower() or "experience" in (await dropdown.get_attribute("aria-label") or "").lower():
                            await dropdown.select_option(index=min(3, len(options)-1), timeout=2000)
                        else:
                            await dropdown.select_option(index=1, timeout=2000)
            except:
                continue  # Skip problematic dropdowns

        # Handle radio buttons - More resilient
        radio_groups = await page.locator("fieldset").all()
        for group in radio_groups:
            try:
                if await group.is_visible():
                    radios = group.locator("input[type='radio']")
                    labels = await group.locator("label").all_text_contents()
                    if "Yes" in labels and "No" in labels:
                        yes_radio = radios.nth(labels.index("Yes"))
                        if await yes_radio.is_visible() and await yes_radio.is_enabled() and not await yes_radio.is_checked():
                            await yes_radio.check(timeout=2000)
            except:
                continue

        # Number fields - More resilient
        number_inputs = await page.locator("input[type='text'], input[type='number']").all()
        for input_box in number_inputs:
            try:
                if await input_box.is_visible() and await input_box.is_enabled():
                    placeholder = (await input_box.get_attribute("placeholder") or "").lower()
                    aria_label = (await input_box.get_attribute("aria-label") or "").lower()
                    value = await input_box.input_value()
                    if ("year" in placeholder or "year" in aria_label or "experience" in aria_label) and not value:
                        await input_box.fill("2", timeout=2000)
            except:
                continue

    except Exception as e:
        print(f"⚠️ Non-critical error during auto-fill: {e}")
        # Don't raise the exception, just continue


async def auto_fill_common_fields(page):
    """Fill all empty fields on the current page and return True if successful"""
    try:
        filled_count = 0
        
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
            try:
                if await page.locator(selector).count() > 0:
                    element = page.locator(selector).first
                    if await element.is_visible() and await element.is_enabled():
                        current_value = await element.input_value()
                        if not current_value.strip():
                            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                            if await element.get_attribute("type") == "radio":
                                await element.check(timeout=2000)
                            elif await element.is_editable():
                                await element.fill("Yes", timeout=2000)
                            elif tag_name == "select":
                                await element.select_option(label="Yes", timeout=2000)
                            filled_count += 1
                            break
            except:
                continue

        # Willing to relocate
        relocate_selectors = [
            "input[aria-label*='willing to relocate']",
            "label:has-text('relocate') input[type='checkbox']",
            "label:has-text('relocate') input[type='radio']"
        ]
        
        for selector in relocate_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    element = page.locator(selector).first
                    if await element.is_visible() and await element.is_enabled() and not await element.is_checked():
                        await element.check(timeout=2000)
                        filled_count += 1
                        break
            except:
                continue

            # Fill all empty text/number inputs
        text_inputs = await page.locator("input[type='text'], input[type='number']").all()
        for input_box in text_inputs:
            try:
                if await input_box.is_visible() and await input_box.is_enabled():
                    current_value = await input_box.input_value()
                    if not current_value.strip():
                        # Get all possible identifying attributes
                        placeholder = (await input_box.get_attribute("placeholder") or "").lower()
                        aria_label = (await input_box.get_attribute("aria-label") or "").lower()
                        input_id = await input_box.get_attribute("id")
                        
                        # Try to find associated label text
                        label_text = ""
                        if input_id:
                            # Find label with matching 'for' attribute
                            label = page.locator(f"label[for='{input_id}']")
                            if await label.count() > 0:
                                label_text = (await label.text_content() or "").lower()
                        
                        # Determine what to fill based on all available information
                        if ("salary" in placeholder or "salary" in aria_label or "salary" in label_text):
                            await input_box.fill("100000", timeout=2000)
                        elif ("year" in placeholder or "year" in aria_label or "year" in label_text or 
                            "experience" in aria_label or "experience" in label_text):
                            await input_box.fill("2", timeout=2000)
                        elif ("city" in placeholder or "city" in aria_label or "city" in label_text):
                            await input_box.fill("Boston", timeout=2000)
                        else:
                            # Only fill N/A if we're sure it's not a special field
                            if not label_text.strip():  # No label means it's probably not important
                                await input_box.fill("N/A", timeout=2000)
                            else:
                                print(f"⚠️ Found labeled input but couldn't determine type: {label_text}")
                        filled_count += 1
            except Exception as e:
                print(f"⚠️ Error filling input: {e}")
                continue

        # Handle dropdowns
        dropdowns = await page.locator("select").all()
        for dropdown in dropdowns:
            try:
                if await dropdown.is_visible() and await dropdown.is_enabled():
                    current_value = await dropdown.input_value()
                    if not current_value.strip():
                        options = await dropdown.locator("option").all_text_contents()
                        options_lower = [opt.strip().lower() for opt in options]
                        
                        if "yes" in options_lower:
                            await dropdown.select_option(label="Yes", timeout=2000)
                        elif "no" in options_lower:
                            await dropdown.select_option(label="No", timeout=2000)
                        else:
                            await dropdown.select_option(index=1, timeout=2000)
                        filled_count += 1
            except:
                continue

        print(f"ℹ️ Filled {filled_count} fields on this page")
        return True

    except Exception as e:
        print(f"⚠️ Error in auto_fill_common_fields: {e}")
        return False


async def handle_application_flow(page):
    """Handle the complete application flow"""
    max_pages = 10  # Safety limit
    current_page = 0
    
    while current_page < max_pages:
        current_page += 1
        print(f"📄 Processing page {current_page} of application")
        
        # First try to fill all empty fields on this page
        fill_success = await auto_fill_common_fields(page)
        if not fill_success:
            print("⚠️ Failed to fill fields, aborting application")
            return False
        
        # Check for submit button (highest priority)
        submit_button = page.locator("button:has-text('Submit application')")
        if await submit_button.count() > 0:
            await submit_button.click()
            print("✅ Application submitted successfully")
            return True
            
        # Check for review button
        review_button = page.locator("button:has-text('Review')")
        if await review_button.count() > 0:
            await review_button.click()
            await asyncio.sleep(2)
            continue
            
        # Check for next button
        next_button = page.locator("button[data-easy-apply-next-button]")
        if await next_button.count() > 0:
            await next_button.click()
            await asyncio.sleep(2)
            continue
            
        # If no navigation buttons found
        print("⚠️ No navigation buttons found on page")
        break
        
    print(f"⚠️ Reached maximum page limit ({max_pages}) without submission")
    return False


async def auto_apply_linkedin_jobs(keywords, job_type):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=50)
            context = await browser.new_context(storage_state="linkedin_session.json")
            page = await context.new_page()

            location = "United States"
            jobs_applied = 0
            max_applications = 20

            for kw in keywords.split(","):
                query = kw.strip().replace(" ", "%20")
                url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location={location}&f_TPR=r86400&f_AL=true"
                
                try:
                    await page.goto(url, timeout=15000)
                    await asyncio.sleep(3)
                except Exception as nav_error:
                    print(f"❌ Failed to navigate to LinkedIn search URL: {nav_error}")
                    continue

                try:
                    job_cards = await page.locator(".job-card-container--clickable").all()
                except Exception as card_error:
                    print(f"❌ Failed to load job cards: {card_error}")
                    continue

                for card in job_cards:
   
                    try:
                        # Handle any modals that might be open
                        if await page.locator(".artdeco-modal__dismiss").count() > 0:
                            await page.locator(".artdeco-modal__dismiss").first.click()
                            await asyncio.sleep(0.5)
                            if await page.locator("button:has-text('Discard')").count() > 0:
                                await page.locator("button:has-text('Discard')").click()
                                await asyncio.sleep(0.5)

                        await card.scroll_into_view_if_needed()
                        await card.click()
                        await asyncio.sleep(2)

                        # Get job details
                        title_el = page.locator(".job-details-jobs-unified-top-card__job-title h1")
                        company_el = page.locator(".job-details-jobs-unified-top-card__company-name a")
                        title = await title_el.text_content() if await title_el.count() > 0 else "Unknown"
                        company = await company_el.text_content() if await company_el.count() > 0 else "Unknown"
                        job_url = page.url

                        print(f"🔍 Checking job: {title} at {company}")

                        # Check for Easy Apply
                        easy_apply_button = page.locator(".artdeco-button:has(span:text('Easy Apply'))")
                        if await easy_apply_button.count() > 0 and await easy_apply_button.first.is_visible():
                            print(f"✅ Found Easy Apply for: {title} at {company}")
                            await easy_apply_button.first.click()
                            await asyncio.sleep(1.5)

                            # Handle the complete application flow
                            success = await handle_application_flow(page)
                            
                            if success:
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
                                log_job_to_sheet({
                                    "title": title.strip(),
                                    "company": company.strip(),
                                    "url": job_url,
                                    "platform": "LinkedIn",
                                    "status": "Failed ❌",
                                    "notes": "Application flow didn't complete"
                                })

                            # Close any remaining modals
                            if await page.locator(".artdeco-modal__dismiss").count() > 0:
                                await page.locator(".artdeco-modal__dismiss").first.click()
                                await asyncio.sleep(0.5)
                                if await page.locator("button:has-text('Discard')").count() > 0:
                                    await page.locator("button:has-text('Discard')").click()

                        await asyncio.sleep(1)
                    except Exception as e:
                        print(f"⚠️ Error processing job card: {e}")
                        continue

            await browser.close()
            return {"message": f"Auto-applied to {jobs_applied} Easy Apply jobs on LinkedIn."}

    except Exception as fatal_error:
        print(f"💥 Fatal error in auto-apply: {fatal_error}")
        return {"message": "Failed to complete LinkedIn auto-apply run."}