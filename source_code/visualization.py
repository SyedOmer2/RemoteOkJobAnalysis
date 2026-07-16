"""
visualization.py
------------------
This file turns the cleaned job data into 4 simple, readable charts:
1. Top 10 Skills (bar chart)
2. Top Job Titles (horizontal bar chart)
3. Job Type Distribution (pie chart)
4. Top Hiring Companies (bar chart)

We keep charts simple on purpose - clear beats fancy.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt


def get_top_skills(df, top_n=10):
    """
    Counts how often each skill appears across all jobs.

    df: cleaned DataFrame
    top_n: how many top skills to return
    Returns: a pandas Series of skill counts
    """
    # Each "skills" cell looks like "python, aws, sql" - split it into a list
    all_skills = df["skills"].str.split(", ")

    # Flatten the list of lists into one long list of individual skills
    flat_skills = [skill for skills in all_skills for skill in skills if skill != ""]

    skill_counts = pd.Series(flat_skills).value_counts()
    return skill_counts.head(top_n)


def chart_top_skills(df, output_folder):
    """
    Creates a bar chart of the top 10 most requested skills.
    """
    top_skills = get_top_skills(df, top_n=10)

    plt.figure(figsize=(10, 6))
    plt.bar(top_skills.index, top_skills.values, color="steelblue")
    plt.title("Top 10 Skills in Demand")
    plt.xlabel("Skill")
    plt.ylabel("Number of Job Postings")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    save_path = os.path.join(output_folder, "top_skills.png")
    plt.savefig(save_path)
    plt.close()
    print(f"Saved chart: {save_path}")


def chart_top_job_titles(df, output_folder):
    """
    Creates a horizontal bar chart of the most common job titles.
    """
    top_titles = df["title"].value_counts().head(10)

    plt.figure(figsize=(10, 6))
    plt.barh(top_titles.index, top_titles.values, color="mediumseagreen")
    plt.title("Top 10 Job Titles")
    plt.xlabel("Number of Postings")
    plt.gca().invert_yaxis()  # largest bar on top
    plt.tight_layout()

    save_path = os.path.join(output_folder, "top_job_titles.png")
    plt.savefig(save_path)
    plt.close()
    print(f"Saved chart: {save_path}")


def chart_job_type_distribution(df, output_folder):
    """
    Creates a pie chart showing the split of job types.
    Since RemoteOK stores job type inside tags, we approximate this
    by checking for common type keywords.
    """
    def classify_job_type(tags_text):
        tags_text = tags_text.lower()
        if "contract" in tags_text:
            return "Contract"
        elif "part time" in tags_text or "part-time" in tags_text:
            return "Part-Time"
        elif "internship" in tags_text or "intern" in tags_text:
            return "Internship"
        else:
            return "Full-Time"

    job_types = df["job_type"].apply(classify_job_type)
    type_counts = job_types.value_counts()

    plt.figure(figsize=(7, 7))
    plt.pie(type_counts.values, labels=type_counts.index, autopct="%1.1f%%",
            colors=["cornflowerblue", "salmon", "gold", "lightgreen"])
    plt.title("Job Type Distribution")
    plt.tight_layout()

    save_path = os.path.join(output_folder, "job_type_distribution.png")
    plt.savefig(save_path)
    plt.close()
    print(f"Saved chart: {save_path}")


def chart_top_companies(df, output_folder):
    """
    Creates a bar chart of the companies hiring the most.
    """
    top_companies = df["company"].value_counts().head(10)

    plt.figure(figsize=(10, 6))
    plt.bar(top_companies.index, top_companies.values, color="darkorange")
    plt.title("Top 10 Hiring Companies")
    plt.xlabel("Company")
    plt.ylabel("Number of Job Postings")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    save_path = os.path.join(output_folder, "top_companies.png")
    plt.savefig(save_path)
    plt.close()
    print(f"Saved chart: {save_path}")


def generate_all_charts(cleaned_file_path, output_folder):
    """
    Runs all 4 chart functions using the cleaned data.

    cleaned_file_path: path to cleaned_jobs.csv
    output_folder: folder where chart images should be saved
    """
    df = pd.read_csv(cleaned_file_path)

    # Make sure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    chart_top_skills(df, output_folder)
    chart_top_job_titles(df, output_folder)
    chart_job_type_distribution(df, output_folder)
    chart_top_companies(df, output_folder)

    print("All charts generated successfully.")
