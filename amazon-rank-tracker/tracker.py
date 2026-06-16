"""
Amazon Keyword Rank Tracker
===========================

Checks where your products rank in Amazon search results for the keywords you
care about, and saves every check to a CSV you can open in Excel or Google Sheets.

You do NOT need to edit this file. Just:
  1. Put your keywords and ASINs in keywords.csv
  2. Set your API key:  export RAPIDAPI_KEY=your_key_here
  3. Run it:            python tracker.py

Each run adds new rows to rank_history.csv with today's position for every
keyword/ASIN pair. Run it once a day (or set up a daily schedule) and you'll
build a history of how your rankings move over time.

Get a free API key here:
https://rapidapi.com/flybyapi1/api/real-time-amazon-data-the-most-complete
"""

import csv
import os
import sys
import time
from datetime import date

import requests

# ── Settings (sensible defaults — change only if you want to) ──────────────
API_KEY = os.environ.get("RAPIDAPI_KEY", "")
API_HOST = "real-time-amazon-data-the-most-complete.p.rapidapi.com"
SEARCH_URL = f"https://{API_HOST}/search"

INPUT_FILE = "keywords.csv"        # what to track
OUTPUT_FILE = "rank_history.csv"   # where results are saved
PAGES_TO_CHECK = 3                 # how deep to look (3 pages ≈ top ~48 results)
PAUSE_SECONDS = 1                  # be polite between requests


def find_rank(keyword, asin, marketplace):
    """Search a keyword and return the position of `asin`, or None if not found."""
    position = 0  # running count across pages

    for page in range(1, PAGES_TO_CHECK + 1):
        params = {
            "query": keyword,
            "marketplace": marketplace,
            "page": page,
            "sort": "relevanceblender",
        }
        headers = {
            "X-RapidAPI-Key": API_KEY,
            "X-RapidAPI-Host": API_HOST,
        }

        response = requests.get(SEARCH_URL, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        products = response.json().get("data", {}).get("products", [])

        if not products:
            break  # no more results

        for product in products:
            position += 1
            if product.get("asin", "").upper() == asin.upper():
                return {
                    "rank": position,
                    "page": page,
                    "title": product.get("product_title", ""),
                }

        time.sleep(PAUSE_SECONDS)

    return None  # not found in the pages we checked


def main():
    if not API_KEY:
        sys.exit("Missing API key. Run:  export RAPIDAPI_KEY=your_key_here")

    # Read the keywords you want to track
    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        targets = list(csv.DictReader(f))

    if not targets:
        sys.exit(f"No rows found in {INPUT_FILE}. Add at least one keyword.")

    today = date.today().isoformat()
    rows = []

    for t in targets:
        keyword = t["keyword"].strip()
        asin = t["asin"].strip()
        marketplace = t.get("marketplace", "com").strip() or "com"

        print(f"Checking '{keyword}' for {asin} ({marketplace}) ...", end=" ")
        try:
            result = find_rank(keyword, asin, marketplace)
        except requests.RequestException as e:
            print(f"error: {e}")
            continue

        if result:
            print(f"rank #{result['rank']} (page {result['page']})")
            rows.append([today, keyword, asin, marketplace,
                         result["rank"], result["page"], result["title"]])
        else:
            print(f"not in top {PAGES_TO_CHECK} pages")
            rows.append([today, keyword, asin, marketplace,
                         "", "", "not found"])

    # Append results to the history file (write a header the first time)
    file_exists = os.path.isfile(OUTPUT_FILE)
    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["date", "keyword", "asin", "marketplace",
                             "rank", "page", "product_title"])
        writer.writerows(rows)

    print(f"\nDone. Saved {len(rows)} rows to {OUTPUT_FILE}.")
    print("Open it in Excel or Google Sheets to see your ranking history.")


if __name__ == "__main__":
    main()
