# === backend/orchestrator.py ===
import asyncio
import requests
from playwright.async_api import async_playwright
from greenhouse_apply import apply_to_greenhouse_job

AIRTABLE_API_KEY = "pat1neehTe4EK0xHI.18f55197cb6d9352ed432aa4e1fdc6e80985fc2ac59a496ffb633192a35ed24d"
BASE_ID = "app5wRRenyunGYeHQ"
TABLE_ID = "tblU11SyFXvl8resN"
VIEW = "Grid view"
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

async def get_airtable_jobs():
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}?view={VIEW}&pageSize=10"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    if "records" in data and len(data["records"]):
        return [record["fields"] for record in data["records"] if "Apply" in record["fields"]]
    return []

async def extract_greenhouse_url(intermediate_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="jobright_session.json")
        page = await context.new_page()

        try:
            await page.goto(intermediate_url)
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(1.5)

            # ✅ Already on Greenhouse application form
            if "greenhouse.io" in page.url and await page.locator("form[action*='apply']").count() > 0:
                print("✅ Already on Greenhouse application form.")
                return page.url

            # 🔁 Step 1: Click Apply Now
            apply_selector = "button:has-text('Apply Now'), a:has-text('Apply Now')"
            if await page.locator(apply_selector).count() > 0:
                print("👉 Clicking 'Apply Now'")
                await page.click(apply_selector)
                await asyncio.sleep(2)

            # 🔁 Step 2: Click "No, continue to apply" and wait for new tab
            continue_selector = "button:has-text('No, continue to apply'), a:has-text('No, continue to apply')"
            if await page.locator(continue_selector).count() > 0:
                print("👉 Clicking 'No, continue to apply'")
                async with context.expect_page() as new_page_info:
                    await page.click(continue_selector)
                new_page = await new_page_info.value
                await new_page.wait_for_load_state("load")
                await asyncio.sleep(2)
                final_url = new_page.url
            else:
                final_url = page.url

            print(f"🌐 Final URL after clicks: {final_url}")

            if "greenhouse.io" in final_url:
                return final_url
            else:
                print("❌ Final URL is not a Greenhouse job")
                return None

        except Exception as e:
            print(f"⚠️ Error while extracting Greenhouse URL: {e}")
            return None
        finally:
            await browser.close()




async def orchestrate_airtable_applications():
    jobs = await get_airtable_jobs()
    if not jobs:
        print("❌ No job found in Airtable.")
        return

    for job in jobs:
        print(f"🔗 Intermediate job link: {job.get('Apply')}")
        final_url = await extract_greenhouse_url(job["Apply"])
        if final_url:
            print(f"✅ Final Greenhouse URL: {final_url}")
            job["Apply"] = final_url
            await apply_to_greenhouse_job(job)
        else:
            print("⏭️ Not a Greenhouse job. Trying next...")

    print("❌ No Greenhouse jobs found in the current Airtable page.")

# Example usage:
# asyncio.run(orchestrate_airtable_applications())
