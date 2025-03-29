# === backend/main.py ===
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from job_scraper import scrape_jobs
from google_sheets import log_job_to_sheet
from linkedin_apply import auto_apply_linkedin_jobs
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobRequest(BaseModel):
    keywords: str  # comma-separated values
    job_type: str  # remote, onsite, hybrid

@app.post("/apply")
async def apply_jobs(req: JobRequest):
    jobs = scrape_jobs(req.keywords, req.job_type)
    for job in jobs:
        log_job_to_sheet(job)
    return {"message": f"Processed {len(jobs)} jobs"}

@app.post("/apply/linkedin")
async def apply_linkedin(req: JobRequest):
    results = await auto_apply_linkedin_jobs(req.keywords, req.job_type)
    return results

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
