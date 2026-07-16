"""
scraper.py
-----------
Downloads job listings from RemoteOK and returns a list of job dictionaries.

Scraping strategy:
1. Collect job listings in batches (~50 per batch).
2. Fetch each job's description page and extract technical skills from the text.
3. Store listing labels separately in `tags`; `skills` holds description-based skills.

Ethical rules (from robots.txt and project guidelines):
- Wait 1 second between every request (Crawl-delay: 1)
- Limited to 1-10 batches per run (about 50-500 jobs), not the whole site
- Educational use only
"""

import time
import json
import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://remoteok.com/"
JSON_FEED_URL = "https://remoteok.com/remote-jobs.json"
JOBS_PER_BATCH = 50

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Educational Scraping Project - BCA Student)"
}

# Technical skills searched inside job descriptions (longer phrases first).
SKILL_PATTERNS = [
    ("machine learning", r"\bmachine learning\b"),
    ("data science", r"\bdata science\b"),
    ("power bi", r"\bpower bi\b"),
    ("node.js", r"\bnode\.?js\b"),
    ("react", r"\breact\.?js\b|\breact\b"),
    ("angular", r"\bangular\b"),
    ("vue", r"\bvue\.?js\b|\bvue\b"),
    ("typescript", r"\btypescript\b"),
    ("javascript", r"\bjavascript\b"),
    ("postgresql", r"\bpostgresql\b|\bpostgres\b"),
    ("mongodb", r"\bmongodb\b"),
    ("kubernetes", r"\bkubernetes\b|\bk8s\b"),
    ("tensorflow", r"\btensorflow\b"),
    ("pytorch", r"\bpytorch\b"),
    ("fastapi", r"\bfastapi\b"),
    ("graphql", r"\bgraphql\b"),
    ("elasticsearch", r"\belasticsearch\b"),
    ("terraform", r"\bterraform\b"),
    ("solidity", r"\bsolidity\b"),
    ("ethereum", r"\bethereum\b"),
    ("blockchain", r"\bblockchain\b"),
    ("python", r"\bpython\b"),
    ("django", r"\bdjango\b"),
    ("flask", r"\bflask\b"),
    ("pandas", r"\bpandas\b"),
    ("numpy", r"\bnumpy\b"),
    ("spark", r"\bspark\b|\bpyspark\b"),
    ("tableau", r"\btableau\b"),
    ("docker", r"\bdocker\b"),
    ("kotlin", r"\bkotlin\b"),
    ("golang", r"\bgolang\b"),
    ("ruby", r"\bruby\b"),
    ("scala", r"\bscala\b"),
    ("swift", r"\bswift\b"),
    ("spring", r"\bspring\b"),
    ("mysql", r"\bmysql\b"),
    ("redis", r"\bredis\b"),
    ("kafka", r"\bkafka\b"),
    ("azure", r"\bazure\b"),
    ("linux", r"\blinux\b"),
    ("html", r"\bhtml\b"),
    ("css", r"\bcss\b"),
    ("rust", r"\brust\b"),
    ("php", r"\bphp\b"),
    ("java", r"\bjava\b(?!script)"),
    ("aws", r"\baws\b|\bamazon web services\b"),
    ("gcp", r"\bgcp\b|\bgoogle cloud\b"),
    ("sql", r"\bsql\b"),
    ("git", r"\bgit\b"),
    ("api", r"\brest api\b|\bapi development\b|\bapi\b"),
    ("c++", r"\bc\+\+\b"),
    ("c#", r"\bc#\b|\bc sharp\b"),
    (".net", r"\b\.net\b|\bdotnet\b"),
    ("excel", r"\bexcel\b"),
    ("agile", r"\bagile\b"),
    ("scrum", r"\bscrum\b"),
    ("ci/cd", r"\bci/cd\b|\bcontinuous integration\b"),
]


def classify_job_type(tags_text):
    """Classifies employment type from listing tags."""
    tags_text = (tags_text or "").lower()
    if "contract" in tags_text:
        return "Contract"
    if "part time" in tags_text or "part-time" in tags_text:
        return "Part-Time"
    if "internship" in tags_text or "intern" in tags_text:
        return "Internship"
    return "Full-Time"


def html_to_text(html_content):
    """Converts HTML job descriptions to plain text."""
    if not html_content:
        return ""
    return BeautifulSoup(html_content, "html.parser").get_text(" ", strip=True)


def extract_skills_from_text(text):
    """Finds technical skills mentioned in a job description."""
    if not text:
        return []

    text_lower = text.lower()
    found_skills = []

    for skill_name, pattern in SKILL_PATTERNS:
        if re.search(pattern, text_lower):
            found_skills.append(skill_name)

    return found_skills


def fetch_job_description(job_url):
    """Downloads and returns the plain-text job description from a job page."""
    if not job_url:
        return ""

    try:
        response = requests.get(job_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        description_tag = soup.select_one("[itemprop=description], .description")
        if description_tag:
            return description_tag.get_text(" ", strip=True)
    except requests.RequestException as error:
        print(f"Could not download description for {job_url}: {error}")

    return ""


def build_description_cache():
    """Builds a URL -> description lookup from the public JSON feed."""
    cache = {}

    try:
        response = requests.get(JSON_FEED_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as error:
        print(f"Could not build description cache: {error}")
        return cache

    for item in data:
        if not isinstance(item, dict):
            continue

        job_url = item.get("url", "") or ""
        if job_url == "":
            continue

        cache[job_url] = html_to_text(item.get("description", "") or "")

    return cache


def enrich_jobs_with_skills(jobs, status_callback=None):
    """
    Fetches each job description and fills the skills field with
    technical skills found in the text.
    """
    total_jobs = len(jobs)
    description_cache = build_description_cache()

    for index, job in enumerate(jobs, start=1):
        if status_callback and (index == 1 or index % 10 == 0 or index == total_jobs):
            status_callback(
                f"Extracting skills ({index}/{total_jobs})... please wait"
            )

        description = job.pop("_description", "")
        if description == "":
            description = description_cache.get(job.get("job_url", ""), "")

        if description == "" and job.get("job_url"):
            description = fetch_job_description(job["job_url"])
            time.sleep(1)

        skills = extract_skills_from_text(description)
        job["skills"] = ", ".join(skills)

    return jobs


def get_page_html(page_number):
    """Downloads the raw HTML of one RemoteOK listing page."""
    if page_number == 1:
        url = BASE_URL
    else:
        url = f"{BASE_URL}/?page={page_number}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as error:
        print(f"Could not download page {page_number}: {error}")
        return None


def get_jobs_batch_html(offset):
    """Downloads one batch of job rows from RemoteOK's paginated listing endpoint."""
    url = f"{BASE_URL}?action=get_jobs&offset={offset}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.RequestException as error:
        print(f"Could not download job batch at offset {offset}: {error}")
        return None


def parse_job_listings(html):
    """Parses job rows from static HTML listing pages."""
    jobs = []

    if html is None:
        return jobs

    soup = BeautifulSoup(html, "html.parser")

    job_rows = [
        row
        for row in soup.find_all("tr", class_="job")
        if "placeholder" not in row.get("class", [])
    ]

    if len(job_rows) == 0:
        job_rows = soup.find_all("tr", attrs={"data-slug": True})

    for row in job_rows:
        job = extract_job_fields(row)
        if job["title"] != "":
            jobs.append(job)

    if len(jobs) == 0:
        jobs = extract_jobs_from_json_ld(soup)

    return jobs


def extract_job_fields(row):
    """Pulls job fields out of one HTML table row."""
    job = {
        "title": "",
        "company": "",
        "location": "",
        "tags": "",
        "skills": "",
        "job_type": "",
        "date_posted": "",
        "job_url": "",
    }

    title_tag = row.find("h2")
    if not title_tag:
        title_tag = row.find(attrs={"itemprop": "title"})
    if not title_tag:
        title_tag = row.select_one(".position h2, .position")
    if title_tag:
        job["title"] = title_tag.get_text(strip=True)

    company_tag = row.find("h3")
    if not company_tag:
        company_tag = row.find(attrs={"itemprop": "name"})
    if not company_tag:
        company_tag = row.select_one(".companyLink h3, .company")
    if company_tag:
        job["company"] = company_tag.get_text(strip=True)
    if job["company"] == "" and row.has_attr("data-company"):
        job["company"] = row["data-company"].strip()

    location_tag = row.find("div", class_="location")
    if location_tag:
        job["location"] = location_tag.get_text(strip=True)

    tag_elements = row.find_all("div", class_="tag")
    if tag_elements:
        tag_list = [tag.get_text(strip=True) for tag in tag_elements]
        job["tags"] = ", ".join(tag_list)

    job["job_type"] = classify_job_type(job["tags"])

    time_tag = row.find("time")
    if time_tag and time_tag.has_attr("datetime"):
        job["date_posted"] = time_tag["datetime"]

    for attr_name in ("data-href", "data-url"):
        if row.has_attr(attr_name):
            path = row[attr_name]
            if path.startswith("http"):
                job["job_url"] = path
            else:
                job["job_url"] = BASE_URL.rstrip("/") + path
            break

    if job["job_url"] == "":
        link_tag = row.select_one("a[itemprop='url'], a.preventLink")
        if link_tag and link_tag.has_attr("href"):
            path = link_tag["href"]
            if path.startswith("http"):
                job["job_url"] = path
            else:
                job["job_url"] = BASE_URL.rstrip("/") + path

    return job


def extract_jobs_from_json_ld(soup):
    """Fallback parser for pages that provide jobs in JSON-LD."""
    jobs = []
    scripts = soup.find_all("script", type="application/ld+json")

    for script in scripts:
        raw_json = script.string
        if not raw_json:
            continue

        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError:
            continue

        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("@type") != "JobPosting":
                continue

            job = {
                "title": item.get("title", "") or "",
                "company": "",
                "location": "",
                "tags": "",
                "skills": "",
                "job_type": item.get("employmentType", "") or "Full-Time",
                "date_posted": item.get("datePosted", "") or "",
                "job_url": item.get("url", "") or "",
            }

            hiring_org = item.get("hiringOrganization")
            if isinstance(hiring_org, dict):
                job["company"] = hiring_org.get("name", "") or ""

            job_location = item.get("jobLocation")
            if isinstance(job_location, dict):
                address = job_location.get("address")
                if isinstance(address, dict):
                    job["location"] = (
                        address.get("addressLocality")
                        or address.get("addressCountry")
                        or ""
                    )

            description = item.get("description", "")
            if description:
                job["_description"] = html_to_text(description)

            if job["title"] != "":
                jobs.append(job)

    return jobs


def deduplicate_jobs(jobs):
    """Removes duplicate jobs before cleaning, using title + company + URL."""
    seen = set()
    unique_jobs = []

    for job in jobs:
        key = (
            job.get("title", "").strip().lower(),
            job.get("company", "").strip().lower(),
            job.get("job_url", "").strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        unique_jobs.append(job)

    return unique_jobs


def scrape_jobs_from_batches(number_of_batches, status_callback=None):
    """
    Fetches paginated job batches (~50 jobs each) until the requested
    number of batches is collected or no more jobs are returned.
    """
    all_jobs = []

    for batch_number in range(number_of_batches):
        offset = batch_number * JOBS_PER_BATCH

        if status_callback:
            status_callback(
                f"Fetching batch {batch_number + 1} of {number_of_batches} "
                f"(~{JOBS_PER_BATCH} jobs each)..."
            )

        html = get_jobs_batch_html(offset)
        jobs_in_batch = parse_job_listings(html)

        if len(jobs_in_batch) == 0:
            break

        all_jobs.extend(jobs_in_batch)
        time.sleep(1)

    return deduplicate_jobs(all_jobs)


def scrape_jobs(number_of_pages, status_callback=None):
    """
    Main scraper entry point.

    number_of_pages: how many batches to scrape (1 to 10)
                     Each batch returns about 50 jobs.
                     Example: 6 batches -> about 300 jobs.
    """
    all_jobs = []
    target_jobs = number_of_pages * JOBS_PER_BATCH

    if status_callback:
        status_callback("Checking public HTML listing page...")

    html = get_page_html(1)
    all_jobs.extend(parse_job_listings(html))
    time.sleep(1)

    if len(all_jobs) < target_jobs:
        if status_callback:
            status_callback(
                f"Collecting more jobs in batches (target: {target_jobs})..."
            )
        batch_jobs = scrape_jobs_from_batches(number_of_pages, status_callback)
        all_jobs.extend(batch_jobs)

    all_jobs = deduplicate_jobs(all_jobs)

    if len(all_jobs) == 0:
        if status_callback:
            status_callback("No batch jobs found, using JSON feed fallback...")
        all_jobs = fetch_jobs_from_json_feed(target_jobs)

    if status_callback:
        status_callback(
            f"Found {len(all_jobs)} jobs. Now reading descriptions for skills..."
        )

    all_jobs = enrich_jobs_with_skills(all_jobs, status_callback)

    if status_callback:
        status_callback(f"Finished scraping. Collected {len(all_jobs)} jobs with skills.")

    return all_jobs


def fetch_jobs_from_json_feed(limit):
    """Reads RemoteOK's public JSON feed and maps it to project fields."""
    try:
        response = requests.get(JSON_FEED_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        print(f"Could not download JSON feed: {error}")
        return []
    except ValueError as error:
        print(f"Could not parse JSON feed: {error}")
        return []

    jobs = []
    for item in data:
        if not isinstance(item, dict):
            continue

        title = item.get("position", "") or ""
        company = item.get("company", "") or ""
        if title == "" and company == "":
            continue

        tags = item.get("tags", [])
        if isinstance(tags, list):
            tags_text = ", ".join(str(tag).strip() for tag in tags if tag)
        else:
            tags_text = str(tags).strip() if tags else ""

        description = html_to_text(item.get("description", "") or "")

        jobs.append(
            {
                "title": title,
                "company": company,
                "location": item.get("location", "") or "",
                "tags": tags_text,
                "skills": "",
                "job_type": classify_job_type(tags_text),
                "date_posted": item.get("date", "") or "",
                "job_url": item.get("url", "") or "",
                "_description": description,
            }
        )

        if len(jobs) >= limit:
            break

    return jobs
