
import os
import re
import requests

from html import unescape
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID", "").strip()
APP_KEY = os.getenv("ADZUNA_APP_KEY", "").strip()
COUNTRY = os.getenv("ADZUNA_COUNTRY", "us").strip().lower()

API_URL = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/1"


def clean_text(text):
    text = re.sub(r"<[^>]*>", " ", text or "")
    return re.sub(r"\s+", " ", unescape(text)).strip()


def search_jobs(keyword, limit=5):
    """Search Adzuna using the job title entered by the user."""

    if not keyword or not keyword.strip():
        return []

    if not APP_ID or not APP_KEY:
        print("Missing Adzuna API credentials in .env")
        return []

    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": min(max(int(limit), 1), 20),
        "what": keyword.strip(),
        "what_or": "remote work from home",
        "content-type": "application/json",
    }

    try:
        response = requests.get(API_URL, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

    except requests.RequestException as error:
        print(f"Adzuna API error: {error}")
        return []
    except (ValueError, TypeError) as error:
        print(f"Invalid input or API response: {error}")
        return []

    jobs = []
    seen_urls = set()

    for job in data.get("results", []):
        title = job.get("title") or "Unknown"
        company = (job.get("company") or {}).get(
            "display_name", "Unknown"
        )
        location = (job.get("location") or {}).get(
            "display_name", "Not specified"
        )
        description = clean_text(job.get("description", ""))
        url = job.get("redirect_url", "")

        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)

        jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "url": url,
            "description": description,
        })

    return jobs


if __name__ == "__main__":
    keyword = input("Enter the job title you want to search for: ").strip()

    for index, job in enumerate(search_jobs(keyword), start=1):
        print(f"\n{index}. {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"URL: {job['url']}")
