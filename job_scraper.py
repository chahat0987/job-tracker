import requests
from bs4 import BeautifulSoup
import sqlite3
import csv
import time

BASE_URL = "https://www.fresheroffcampus.com/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

# ------------------------
# DATABASE SETUP
# ------------------------
conn = sqlite3.connect("jobs.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    source_link TEXT UNIQUE,
    apply_link TEXT
)
""")

conn.commit()

# ------------------------
# STEP 1: SCRAPE HOMEPAGE
# ------------------------
response = requests.get(BASE_URL, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

articles = soup.find_all("article", class_=lambda x: x and "entry-card" in x)

print("Jobs Found:", len(articles))
print("-" * 60)

for article in articles:

    title_tag = article.find("h1", class_="entry-title")

    if not title_tag:
        continue

    link_tag = title_tag.find("a")
    if not link_tag:
        continue

    title = link_tag.text.strip()
    source_link = link_tag["href"]

    # ------------------------
    # STEP 2: SCRAPE JOB PAGE
    # ------------------------
    try:
        job_response = requests.get(source_link, headers=headers)
        job_soup = BeautifulSoup(job_response.text, "html.parser")

        real_apply_link = None

        all_links = job_soup.find_all("a", href=True)

        for a in all_links:
            href = a["href"]
            if "careers" in href or "apply" in href:
                real_apply_link = href
                break

        # small delay (good practice)
        time.sleep(1)

    except Exception as e:
        print("Error scraping job page:", e)
        real_apply_link = None

    # ------------------------
    # SAVE TO DATABASE
    # ------------------------
    try:
        cursor.execute(
            "INSERT INTO jobs (title, source_link, apply_link) VALUES (?, ?, ?)",
            (title, source_link, real_apply_link)
        )
        conn.commit()
        print("New Job Added:", title)

    except sqlite3.IntegrityError:
        print("Already Exists:", title)

print("-" * 60)

# ------------------------
# EXPORT TO CSV
# ------------------------
cursor.execute("SELECT title, source_link, apply_link FROM jobs")
rows = cursor.fetchall()

with open("jobs.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Job Title", "Source Link", "Apply Link"])
    writer.writerows(rows)

print("CSV file updated successfully!")

conn.close()
