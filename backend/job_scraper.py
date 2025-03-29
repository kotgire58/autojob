import requests

def scrape_jobs(keywords, job_type):
    jobs = []
    response = requests.get("https://remoteok.com/api")
    if response.status_code == 200:
        for item in response.json():
            if not isinstance(item, dict) or "position" not in item:
                continue
            if keywords.lower() in item.get("position", "").lower():
                jobs.append({
                    "title": item.get("position", "Unknown"),
                    "company": item.get("company", "Unknown"),
                    "url": item.get("url", ""),
                    "platform": "RemoteOK",
                    "status": "Manual Review",
                    "notes": "Review for extra requirements"
                })
    return jobs