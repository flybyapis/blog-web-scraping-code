"""
Export a Google Maps List to CSV. FlyByAPIs.

Pulls a full list of businesses from a Google Maps search via the FlyByAPIs
Google Maps Extractor API and writes it to a CSV you can open in Excel or
Google Sheets. One request returns up to 200 businesses, so the script
paginates with `offset` to collect lists larger than that.

Only dependency: requests. Everything else is the Python standard library.

Usage:
    export RAPIDAPI_KEY="your_key_here"
    python export.py                              # coffee shops in Austin, 300 rows
    python export.py "dentists in Chicago" 500    # custom query + target count

Get a free key (100 requests/month):
    https://rapidapi.com/flybyapi1/api/google-maps-extractor2
"""

import csv
import json
import os
import sys
import time

import requests

API_HOST = "google-maps-extractor2.p.rapidapi.com"
URL = f"https://{API_HOST}/locate_and_search"

# The API returns at most 200 results per request. To get more, page with offset.
MAX_PAGE_SIZE = 200

HEADERS = {
    "X-RapidAPI-Key": os.environ.get("RAPIDAPI_KEY", ""),
    "X-RapidAPI-Host": API_HOST,
}

# detailed_address is a nested object; we give each part its own column.
ADDRESS_PARTS = ["street", "district", "city", "state", "zip_code", "country"]


def fetch_page(query: str, offset: int, limit: int = MAX_PAGE_SIZE) -> dict:
    """Fetch one page of results from /locate_and_search."""
    params = {
        "query": query,
        "language": "en",
        "country": "us",
        "limit": min(limit, MAX_PAGE_SIZE),   # never ask for more than the cap
        "offset": offset,
    }
    resp = requests.get(URL, headers=HEADERS, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def collect_businesses(query: str, target: int = 300, page_size: int = MAX_PAGE_SIZE) -> list[dict]:
    """Page through the search results until we hit `target` unique businesses."""
    seen: set[str] = set()
    rows: list[dict] = []
    offset = 0

    while len(rows) < target:
        payload = fetch_page(query, offset, page_size)

        if not payload.get("status"):
            print(f"API returned status=false at offset {offset}, stopping.")
            break

        batch = payload.get("data", [])
        if not batch:
            break

        for biz in batch:
            bid = biz.get("google_id") or biz.get("business_id")
            if not bid or bid in seen:
                continue
            seen.add(bid)
            rows.append(biz)

        print(f"offset {offset}: +{len(batch)} results ({len(rows)} unique so far)")

        if len(batch) < page_size:
            break          # last page reached, no point asking for more

        offset += page_size
        time.sleep(1)      # be polite, respect the rate limit

    return rows[:target]


def flatten(biz: dict) -> dict:
    """Flatten one business into a single flat row, keeping every field.

    - detailed_address is expanded into address_street, address_city, etc.
    - lists (categories, about_descriptions) are joined with " | ".
    - nested objects/lists (working_hours, about, price_breakdown) are kept
      losslessly as JSON strings so nothing is dropped.
    """
    row = {}
    for key, val in biz.items():
        if key == "detailed_address":
            parts = val or {}
            for part in ADDRESS_PARTS:
                row[f"address_{part}"] = parts.get(part, "")
        elif isinstance(val, list) and all(isinstance(x, str) for x in val):
            row[key] = " | ".join(val)
        elif isinstance(val, (list, dict)):
            row[key] = json.dumps(val, ensure_ascii=False) if val else ""
        else:
            row[key] = "" if val is None else val
    return row


def write_csv(businesses: list[dict], path: str = "google_maps_list.csv") -> None:
    """Write every field the API returns to a UTF-8 CSV (one row per business)."""
    rows = [flatten(b) for b in businesses]

    # Build the column list from the union of all keys, preserving first-seen order.
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"Wrote {len(rows)} rows x {len(columns)} columns to {path}")


def main() -> None:
    if not HEADERS["X-RapidAPI-Key"]:
        sys.exit("Set RAPIDAPI_KEY first:  export RAPIDAPI_KEY=your_key_here")

    query = sys.argv[1] if len(sys.argv) > 1 else "coffee shops in Austin"
    target = int(sys.argv[2]) if len(sys.argv) > 2 else 300

    print(f"Searching: {query!r} (target {target} businesses)\n")
    businesses = collect_businesses(query, target=target)
    write_csv(businesses)


if __name__ == "__main__":
    main()
