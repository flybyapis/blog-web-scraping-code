"""
Scrape Google Maps search results via the FlyByAPIs Google Maps Extractor API.

Same data as the Selenium scraper in ../selenium-scraper, plus review counts
and full review text, from plain HTTP requests. Up to 200 businesses per
request; pages with `offset` for larger lists.

Usage:
    export RAPIDAPI_KEY="your_key_here"
    python scraper.py                              # coffee shops in Austin
    python scraper.py "dentists in Chicago" 400    # custom query + target count

Get a free key (100 requests/month):
    https://rapidapi.com/flybyapi1/api/google-maps-extractor2
"""

import csv
import os
import sys
import time

import requests

API_HOST = "google-maps-extractor2.p.rapidapi.com"
HEADERS = {
    "X-RapidAPI-Key": os.environ.get("RAPIDAPI_KEY", ""),
    "X-RapidAPI-Host": API_HOST,
}

PAGE_SIZE = 200  # API maximum per request

COLUMNS = [
    "name", "rating", "reviews_count", "main_category", "full_address",
    "full_phone", "website_url", "latitude", "longitude", "google_id",
]


def fetch_page(query: str, offset: int) -> dict:
    resp = requests.get(
        f"https://{API_HOST}/locate_and_search",
        headers=HEADERS,
        params={
            "query": query,
            "country": "us",
            "language": "en",
            "limit": PAGE_SIZE,
            "offset": offset,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def collect(query: str, target: int) -> list[dict]:
    """Page through results with `offset` until we hit `target` unique rows."""
    seen: set[str] = set()
    rows: list[dict] = []
    offset = 0

    while len(rows) < target:
        payload = fetch_page(query, offset)
        if not payload.get("status"):
            print(f"API returned status=false at offset {offset}, stopping.")
            break

        batch = payload.get("data", [])
        if not batch:
            break

        for biz in batch:
            bid = biz.get("google_id")
            if not bid or bid in seen:
                continue
            seen.add(bid)
            rows.append({col: biz.get(col, "") for col in COLUMNS})

        print(f"offset {offset}: +{len(batch)} results ({len(rows)} unique so far)")
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
        time.sleep(1)

    return rows[:target]


def fetch_reviews(business_id: str, limit: int = 20) -> list[dict]:
    """Bonus: pull review text for one business (paginated via next_page_token)."""
    resp = requests.get(
        f"https://{API_HOST}/business_reviews",
        headers=HEADERS,
        params={"business_id": business_id, "limit": limit, "sort_by": "mostRecent"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("data", [])


def main() -> None:
    if not HEADERS["X-RapidAPI-Key"]:
        sys.exit("Set RAPIDAPI_KEY first:  export RAPIDAPI_KEY=your_key_here")

    query = sys.argv[1] if len(sys.argv) > 1 else "coffee shops in Austin"
    target = int(sys.argv[2]) if len(sys.argv) > 2 else 200

    print(f"Searching: {query!r} (target {target} businesses)\n")
    rows = collect(query, target)

    path = "google_maps_results.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {path}")


if __name__ == "__main__":
    main()
