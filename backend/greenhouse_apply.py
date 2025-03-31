# === backend/greenhouse_apply.py ===
from playwright.async_api import async_playwright
import asyncio
from google_sheets import log_job_to_sheet
import os

RESUME_PATH = os.path.abspath("resume.pdf")  # Ensure this file exists

def field_matches(label, *keywords):
    return any(kw in label.lower() for kw in keywords)

async def apply_to_greenhouse_job(job):
    url = job.get("Apply")
    title = job.get("Position Title", "Unknown")
    company = job.get("Company", "Unknown")

    # Profile and extension paths
    profile_path = "/tmp/playwright-simplify-user-data"
    simplify_extension_path = "/Users/kamalkotgire/Library/Application Support/Google/Chrome/Default/Extensions/pbanhockgagggenencehbnadejlgchfc/2.0.61_0"

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=profile_path,
                headless=False,
                args=[
                    f"--disable-extensions-except={simplify_extension_path}",
                    f"--load-extension={simplify_extension_path}"
                ]
            )

            page = await browser.new_page()
            await page.goto(url, timeout=30000)  # Increased timeout
            await asyncio.sleep(5)  # Let page load completely

            print(f"✅ Found Greenhouse application form for {title} at {company}")

            # 🔘 Click Simplify Autofill button
            clicked = False
            try:
                btn = page.locator("#fill-button")
                await btn.wait_for(state="visible", timeout=5000)
                print("⚡ Clicking Simplify Autofill button (#fill-button)...")
                await btn.click()
                await asyncio.sleep(3)
                clicked = True
            except Exception as e:
                print(f"ℹ️ Simplify button not found: {e}")

            if not clicked:
                try:
                    fallback = page.locator("text=Autofill this page")
                    await fallback.wait_for(state="visible", timeout=5000)
                    print("⚡ Clicking Simplify Autofill fallback...")
                    await fallback.click()
                    await asyncio.sleep(3)
                except:
                    print("ℹ️ Could not detect Simplify Autofill — assuming it's already filled.")

            # ⏳ Wait for autofill to complete
            print("⏳ Waiting for autofill to complete...")
            await asyncio.sleep(3)

            # 🛠️ Fill in any fields Simplify missed
            inputs = await page.locator("input[type='text'], input[type='email'], input[type='tel']").all()
            for input_box in inputs:
                name_attr = await input_box.get_attribute("name") or ""
                aria_label = await input_box.get_attribute("aria-label") or ""
                placeholder = await input_box.get_attribute("placeholder") or ""
                field_id = name_attr + aria_label + placeholder

                current_value = await input_box.input_value()
                if current_value.strip():
                    continue  # Already filled

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
                else:
                    await input_box.fill("N/A")

            # 🎯 Handle the custom location dropdown
            try:
                print("📍 Looking for location question...")
                dropdown = page.locator("#question_55023923")
                
                if await dropdown.count() > 0:
                    print("⚡ Found location dropdown - attempting to select 'Yes'")
                    
                    # Method 1: Directly type the value
                    await dropdown.click()
                    await dropdown.fill("Yes")
                    await asyncio.sleep(1)
                    await dropdown.press("Enter")
                    
                    # Verify selection
                    selected_value = await dropdown.input_value()
                    if "yes" not in selected_value.lower():
                        # Method 2: Keyboard navigation fallback
                        print("⚠️ Typing didn't work, trying keyboard navigation")
                        await dropdown.click()
                        await asyncio.sleep(1)
                        await dropdown.press("ArrowDown")
                        await asyncio.sleep(0.5)
                        await dropdown.press("ArrowDown")
                        await asyncio.sleep(0.5)
                        await dropdown.press("Enter")
                    
                    print("✅ Location question handled")
                else:
                    print("⚠️ Could not find location dropdown")
            except Exception as e:
                print(f"⚠️ Error handling location question: {e}")

            # ✅ Submit the form
            submit_btn = page.locator("button[type='submit'], input[type='submit']")
            if await submit_btn.count() > 0:
                print("✅ Submitting application...")
                await submit_btn.first.click()
                await asyncio.sleep(5)  # Wait longer after submission
            else:
                raise Exception("Submit button not found")

            # ✅ Confirm submission
            if await page.locator("text=Your application has been submitted").count() > 0:
                log_job_to_sheet({
                    "title": title,
                    "company": company,
                    "url": url,
                    "platform": "Greenhouse",
                    "status": "Applied ✅",
                    "notes": "Submitted with custom dropdown handling"
                })
                print(f"🎉 Successfully applied to {title} at {company}")
            else:
                await asyncio.sleep(5)  # Wait longer after submission
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

