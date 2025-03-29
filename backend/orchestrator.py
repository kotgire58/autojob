# === backend/orchestrator.py ===
import asyncio
import requests
from playwright.async_api import async_playwright
from greenhouse_apply import apply_to_greenhouse_job

AIRTABLE_API_KEY = "pat1neehTe4EK0xHI.18f55197cb6d9352ed432aa4e1fdc6e80985fc2ac59a496ffb633192a35ed24d"
BASE_ID = "app5wRRenyunGYeHQ"
TABLE_ID = "tblAAY5duCKqCOz61"
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
        browser = await p.chromium.launch(headless=False)  # make it visible
        context = await browser.new_context(storage_state="jobright_session.json")
        page = await context.new_page()

        final_url = None

        try:
            await page.goto(intermediate_url)
            await page.wait_for_load_state("domcontentloaded")

            # Match button or link with text Apply Now
            apply_selector = "button:has-text('Apply Now'), a:has-text('Apply Now')"
            await page.wait_for_selector(apply_selector, timeout=7000)
            await page.click(apply_selector)

            # Wait for redirect
            await page.wait_for_load_state("load")
            await asyncio.sleep(2)
            final_url = page.url

        except Exception as e:
            print(f"⚠️ Error while extracting final URL: {e}")
            final_url = None

        await browser.close()
        return final_url if final_url and "greenhouse.io" in final_url else None


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
            return
        else:
            print("⏭️ Not a Greenhouse job. Trying next...")

    print("❌ No Greenhouse jobs found in the current Airtable page.")

# Example usage:
# asyncio.run(orchestrate_airtable_applications())
