import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1FQOg9YhlkIZGA2h85mImpmKcyFmV2jyKKmn2yZV4g1c"
SHEET_NAME = "Sheet1"

creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

def log_job_to_sheet(job):
    sheet.append_row([
        job["title"],
        job["company"],
        job["url"],
        job["platform"],
        job["status"],
        job["notes"]
    ])
