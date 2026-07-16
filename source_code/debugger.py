"""
debugger.py
------------
Quick diagnostic script for RemoteOK scraping.

Run:
    python debugger.py
"""

import requests
from bs4 import BeautifulSoup

from src.scraper import (
    HEADERS,
    JOBS_PER_BATCH,
    JSON_FEED_URL,
    fetch_jobs_from_json_feed,
    get_jobs_batch_html,
    parse_job_listings,
    scrape_jobs_from_batches,
)

print("=== RemoteOK Scraper Debugger ===\n")

try:
    response = requests.get("https://remoteok.com", headers=HEADERS, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    all_job_rows = soup.find_all("tr", class_="job")
    placeholder_rows = [row for row in all_job_rows if "placeholder" in row.get("class", [])]
    parsed_html_jobs = parse_job_listings(response.text)

    print("HTML status code:", response.status_code)
    print("Static HTML jobs found:", len(parsed_html_jobs))
    print("Placeholder rows on homepage:", len(placeholder_rows))
except requests.RequestException as error:
    print("HTML request failed:", error)

print()

try:
    batch_html = get_jobs_batch_html(0)
    batch_jobs = parse_job_listings(batch_html)
    print("Batch endpoint jobs (offset 0):", len(batch_jobs))
    if batch_jobs:
        print("Sample batch job:", batch_jobs[0]["title"], "-", batch_jobs[0]["company"])
except Exception as error:
    print("Batch request failed:", error)

print()

try:
    six_batches = scrape_jobs_from_batches(6)
    print("Jobs from 6 batches (~300 target):", len(six_batches))
except Exception as error:
    print("Batch scrape test failed:", error)

print()

try:
    json_jobs = fetch_jobs_from_json_feed(limit=5)
    print("JSON feed sample jobs:", len(json_jobs))
    print("JSON feed URL:", JSON_FEED_URL)
    print("Jobs per batch setting:", JOBS_PER_BATCH)
except Exception as error:
    print("JSON feed request failed:", error)

print("\nDone.")
