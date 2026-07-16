"""
cleaner.py
-----------
Cleans scraped job data before analysis or Tableau import.

Two entry points:
- clean_jobs_list(jobs)  — clean scraped jobs directly in memory (used by GUI)
- clean_data(raw_path, cleaned_path)  — clean from a raw CSV file on disk

Cleaning steps:
1. Remove duplicate job entries
2. Handle missing values
3. Standardize text (so "Python" and "python" count as the same thing)
"""

import pandas as pd


def load_raw_data(file_path):
    """
    Reads the raw CSV file into a pandas DataFrame (a table).

    file_path: path to the raw_jobs.csv file
    Returns: a pandas DataFrame
    """
    return pd.read_csv(file_path)


def remove_duplicate_jobs(df):
    """
    Removes jobs that were accidentally scraped more than once.
    We treat two jobs as duplicates if they have the same title,
    company, and job URL.

    df: the DataFrame of jobs
    Returns: a DataFrame with duplicates removed
    """
    before_count = len(df)
    df = df.drop_duplicates(subset=["title", "company", "job_url"])
    after_count = len(df)

    removed = before_count - after_count
    print(f"Removed {removed} duplicate job(s).")

    return df


def handle_missing_values(df):
    """
    Decides what to do with empty fields.

    Rule for this project:
    - If the job title or company is missing, the row is not useful,
      so we drop it.
    - For other fields (location, skills, job_type, date_posted),
      we fill empty values with "Not specified" instead of dropping
      the row, so we don't lose good data unnecessarily.

    df: the DataFrame of jobs
    Returns: a cleaned DataFrame
    """
    # Drop rows where the title or company is missing/blank
    df = df.dropna(subset=["title", "company"])
    df = df[(df["title"].str.strip() != "") & (df["company"].str.strip() != "")]

    # Fill remaining missing fields with a placeholder
    fill_columns = ["location", "tags", "skills", "job_type", "date_posted", "job_url"]
    for column in fill_columns:
        df[column] = df[column].fillna("Not specified")
        df[column] = df[column].replace("", "Not specified")

    return df


def standardize_text(df):
    """
    Makes text consistent so similar values are counted together.
    Example: "React.js" and "ReactJS" should be treated the same way
    for skill-counting purposes.

    df: the DataFrame of jobs
    Returns: a DataFrame with standardized text columns
    """
    # Trim extra whitespace and fix capitalization for readability
    df["title"] = df["title"].str.strip()
    df["company"] = df["company"].str.strip().str.title()
    df["location"] = df["location"].str.strip()

    # Standardize skills: lowercase, remove extra spaces, fix common variants
    def clean_skill_text(skill_text):
        skill_text = skill_text.lower()
        skill_text = skill_text.replace("react.js", "reactjs")
        skill_text = skill_text.replace("node.js", "nodejs")
        return skill_text

    df["skills"] = df["skills"].apply(clean_skill_text)

    return df


def clean_data(raw_file_path, cleaned_file_path):
    """
    Runs the full cleaning pipeline: load, remove duplicates,
    handle missing values, standardize text, then save the result.

    raw_file_path: where raw_jobs.csv is located
    cleaned_file_path: where to save cleaned_jobs.csv
    Returns: the cleaned DataFrame
    """
    df = load_raw_data(raw_file_path)
    df = remove_duplicate_jobs(df)
    df = handle_missing_values(df)
    df = standardize_text(df)

    df.to_csv(cleaned_file_path, index=False)
    print(f"Cleaned data saved to {cleaned_file_path}")

    return df


def clean_jobs_list(jobs, cleaned_file_path=None):
    """
    Cleans scraped jobs directly from memory (without requiring
    a raw CSV file first).

    jobs: list of dictionaries returned by scraper.py
    cleaned_file_path: optional path to save cleaned CSV
    Returns: cleaned DataFrame
    """
    if jobs is None:
        jobs = []

    df = pd.DataFrame(jobs)

    expected_columns = [
        "title",
        "company",
        "location",
        "tags",
        "skills",
        "job_type",
        "date_posted",
        "job_url",
    ]
    for column in expected_columns:
        if column not in df.columns:
            df[column] = ""

    df = df[expected_columns]
    df = remove_duplicate_jobs(df)
    df = handle_missing_values(df)
    df = standardize_text(df)

    if cleaned_file_path:
        df.to_csv(cleaned_file_path, index=False)
        print(f"Cleaned data saved to {cleaned_file_path}")

    return df
