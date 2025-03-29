# === backend/greenhouse_apply.py ===
from playwright.async_api import async_playwright
import asyncio
from google_sheets import log_job_to_sheet
import os

RESUME_PATH = os.path.abspath("resume.pdf")  # Ensure this file exists

def field_matches(label, *keywords):
    return any(kw in label.lower() for kw in keywords)

async def auto_fill_greenhouse_fields(page):
    try:
        # === Fill text fields ===
        inputs = await page.locator("input[type='text'], input[type='email'], input[type='tel']").all()
        for input_box in inputs:
            name_attr = await input_box.get_attribute("name") or ""
            aria_label = await input_box.get_attribute("aria-label") or ""
            placeholder = await input_box.get_attribute("placeholder") or ""
            field_id = name_attr + aria_label + placeholder

            if field_matches(field_id, "name"):
                await input_box.fill("Kamal Kotgire")
            elif field_matches(field_id, "email"):
                await input_box.fill("kamal@example.com")
            elif field_matches(field_id, "phone"):
                await input_box.fill("1234567890")
            elif field_matches(field_id, "linkedin"):
                await input_box.fill("https://www.linkedin.com/in/kamalkotgire")
            elif field_matches(field_id, "github"):
                await input_box.fill("https://github.com/kamalkotgire")
            elif field_matches(field_id, "website"):
                await input_box.fill("https://kamalkotgire.dev")
            elif not await input_box.input_value():
                await input_box.fill("N/A")

        # === Fill textareas ===
        textareas = await page.locator("textarea").all()
        for ta in textareas:
            await ta.fill("I'm excited to apply for this role. Please refer to my resume for more details.")

        # === Upload resume ===
        if await page.locator("input[type='file']").count() > 0:
            await page.set_input_files("input[type='file']", RESUME_PATH)

        # === Handle dropdowns ===
        selects = await page.locator("select").all()
        for sel in selects:
            options = await sel.locator("option").all_text_contents()
            options = [opt.strip() for opt in options if opt.strip()]
            yes_opts = [o for o in options if o.lower() == "yes"]
            if yes_opts:
                await sel.select_option(label=yes_opts[0])
            elif len(options) > 1 and not options[0].lower().startswith("select"):
                await sel.select_option(label=options[1])

        return True

    except Exception as e:
        print(f"⚠️ Error auto-filling Greenhouse form: {e}")
        return False


async def apply_to_greenhouse_job(job):
    url = job.get("Apply")
    title = job.get("Position Title", "Unknown")
    company = job.get("Company", "Unknown")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto(url, timeout=15000)
            await asyncio.sleep(3)

            # Greenhouse form check
            if not await page.locator("form[action*='apply']").count():
                raise Exception("No Greenhouse application form found")

            print(f"✅ Found Greenhouse application form for {title} at {company}")

            filled = await auto_fill_greenhouse_fields(page)
            if not filled:
                raise Exception("Failed to fill fields")

            # Try clicking submit
            submit_btn = page.locator("button[type='submit']")
            if await submit_btn.count() > 0:
                await submit_btn.first.click()
                await asyncio.sleep(3)

            # Log result
            if await page.locator("text=Your application has been submitted").count() > 0:
                log_job_to_sheet({
                    "title": title,
                    "company": company,
                    "url": url,
                    "platform": "Greenhouse",
                    "status": "Applied ✅",
                    "notes": "Submitted successfully"
                })
                print(f"🎉 Applied to {title} at {company}")
            else:
                raise Exception("Submit confirmation not found")

            await browser.close()
    except Exception as e:
        print(f"❌ Failed applying to Greenhouse job {title} at {company}: {e}")
        log_job_to_sheet({
            "title": title,
            "company": company,
            "url": url,
            "platform": "Greenhouse",
            "status": "Skipped ❌",
            "notes": str(e)
        })
