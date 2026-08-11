"""
Export Google reviews to CSV. FlyByAPIs.

Takes one or more business names, finds each one on Google Maps, pulls its full
review history, and writes everything to a single CSV you can open in Excel or
Google Sheets. Works for any public business — you don't need to own the
profile, so client and competitor reviews are fair game.

Two endpoints do the work:
  /locate_and_search  turns "Reading Terminal Market, Philadelphia" into a google_id
  /business_reviews   returns the reviews for that google_id, 20 at a time

The reviews endpoint caps `limit` at 20 no matter what you ask for, so the only
way past the first 20 is the next_token pagination loop in fetch_reviews().

Only dependency: requests. Everything else is the Python standard library.

Usage:
    export RAPIDAPI_KEY="your_key_here"
    python export_reviews.py "Reading Terminal Market, Philadelphia"
    python export_reviews.py "Joe's Pizza, New York" --max 200 --sort mostRecent
    python export_reviews.py --from-file businesses.txt --out client_reviews.csv

Get a free key (100 requests/month):
    https://rapidapi.com/flybyapi1/api/google-maps-extractor2
"""

import argparse
import csv
import datetime
import os
import sys
import time

import requests

API_HOST = "google-maps-extractor2.p.rapidapi.com"
SEARCH_URL = f"https://{API_HOST}/locate_and_search"
REVIEWS_URL = f"https://{API_HOST}/business_reviews"

# The reviews endpoint returns at most 20 per request. Asking for 100 still
# returns 20, so pagination is the only way to get a full review history.
PAGE_SIZE = 20

SORT_OPTIONS = ["mostRecent", "qualityScore", "ratingHighToLow", "ratingLowToHigh"]

COLUMNS = [
    "business_name",
    "business_address",
    "business_rating",
    "business_reviews_count",
    "review_date",
    "review_relative_time",
    "rating",
    "review_text",
    "reviewer_name",
    "reviewer_is_local_guide",
    "reviewer_total_reviews",
    "owner_response_date",
    "owner_response_text",
    "photos_count",
    "language",
    "review_id",
    "review_url",
    "reviewer_profile_url",
]


def headers() -> dict:
    key = os.environ.get("RAPIDAPI_KEY", "")
    if not key:
        sys.exit("Set RAPIDAPI_KEY first:  export RAPIDAPI_KEY=your_key_here")
    return {"x-rapidapi-key": key, "x-rapidapi-host": API_HOST}


def get_json(url: str, params: dict) -> dict:
    """GET a URL and return parsed JSON, failing with a readable message."""
    try:
        resp = requests.get(url, headers=headers(), params=params, timeout=30)
    except requests.RequestException as exc:
        print(f"  network error: {exc}")
        return {}

    if resp.status_code == 401:
        sys.exit("401 Unauthorized — check your RAPIDAPI_KEY.")
    if resp.status_code == 429:
        print("  rate limited (429), waiting 10s...")
        time.sleep(10)
        return get_json(url, params)
    if resp.status_code != 200:
        print(f"  HTTP {resp.status_code}: {resp.text[:200]}")
        return {}

    try:
        return resp.json()
    except ValueError:
        print("  response was not valid JSON")
        return {}


def find_business(query: str) -> dict | None:
    """Resolve a business name to its Google Maps record (including google_id).

    The first result is the match in the overwhelming majority of cases, as long
    as the query includes the city. "Joe's Pizza" is ambiguous; "Joe's Pizza,
    New York" is not.
    """
    payload = get_json(SEARCH_URL, {
        "query": query,
        "language": "en",
        "country": "us",
        "limit": 1,
    })

    results = payload.get("data") or []
    if not results:
        print(f"  no business found for {query!r} — try adding the city")
        return None
    return results[0]


def fetch_reviews(google_id: str, max_reviews: int, sort_by: str) -> list[dict]:
    """Page through every review for one business until we hit max_reviews.

    The API hands back a next_token with each page; feeding it back as
    next_page_token gets the following 20. When the token stops coming, or a
    page arrives empty, we've reached the end of the review history.
    """
    reviews: list[dict] = []
    token = None

    while len(reviews) < max_reviews:
        params = {
            "business_id": google_id,
            "language": "en",
            "country": "us",
            "limit": PAGE_SIZE,
            "sort_by": sort_by,
        }
        if token:
            params["next_page_token"] = token

        payload = get_json(REVIEWS_URL, params)
        batch = payload.get("data") or []
        if not batch:
            break

        reviews.extend(batch)
        print(f"  +{len(batch)} reviews ({len(reviews)} so far)")

        token = payload.get("next_token")
        if not token:
            break          # no more pages
        time.sleep(1)      # be polite, stay inside the rate limit

    return reviews[:max_reviews]


def to_iso_date(timestamp) -> str:
    """Turn the Unix timestamp into a real YYYY-MM-DD date.

    This is the field that makes an export worth having. The `time` field is a
    relative string like "3 months ago", which is useless the moment you try to
    sort, filter by month, or chart reviews over time.
    """
    if not timestamp:
        return ""
    try:
        return datetime.datetime.fromtimestamp(
            int(timestamp), tz=datetime.timezone.utc
        ).strftime("%Y-%m-%d")
    except (ValueError, OSError, OverflowError):
        return ""


def build_row(business: dict, review: dict) -> dict:
    """Flatten one business + one review into a single CSV row."""
    return {
        "business_name": business.get("name", ""),
        "business_address": business.get("full_address") or business.get("address", ""),
        "business_rating": business.get("rating", ""),
        "business_reviews_count": business.get("reviews_count", ""),
        "review_date": to_iso_date(review.get("timestamp")),
        "review_relative_time": review.get("time", ""),
        "rating": review.get("rating", ""),
        # Reviews left as a bare star rating have no text at all.
        "review_text": (review.get("text") or "").replace("\n", " ").strip(),
        "reviewer_name": review.get("user_name", ""),
        "reviewer_is_local_guide": "yes" if review.get("user_is_local_guide") else "no",
        "reviewer_total_reviews": review.get("user_reviews_count", ""),
        "owner_response_date": to_iso_date(review.get("owner_response_timestamp")),
        "owner_response_text": (review.get("owner_response_text") or "").replace("\n", " ").strip(),
        "photos_count": len(review.get("photos") or []),
        "language": review.get("language") or "",
        "review_id": review.get("id", ""),
        "review_url": review.get("url", ""),
        "reviewer_profile_url": review.get("user_profile_url", ""),
    }


def write_csv(rows: list[dict], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {len(rows)} reviews to {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Google reviews to CSV.")
    parser.add_argument("business", nargs="*", help='e.g. "Joe\'s Pizza, New York"')
    parser.add_argument("--from-file", help="text file with one business per line")
    parser.add_argument("--max", type=int, default=100, help="max reviews per business")
    parser.add_argument("--sort", default="mostRecent", choices=SORT_OPTIONS)
    parser.add_argument("--out", default="google_reviews.csv", help="output CSV path")
    args = parser.parse_args()

    queries = list(args.business)
    if args.from_file:
        with open(args.from_file, encoding="utf-8") as f:
            queries += [line.strip() for line in f if line.strip()]
    if not queries:
        parser.error("give at least one business name, or use --from-file")

    rows: list[dict] = []
    for query in queries:
        print(f"\n{query}")
        business = find_business(query)
        if not business:
            continue

        google_id = business.get("google_id")
        if not google_id:
            print("  no google_id on this result, skipping")
            continue

        print(f"  found: {business.get('name')} ({business.get('reviews_count', 0)} reviews total)")
        reviews = fetch_reviews(google_id, args.max, args.sort)
        rows.extend(build_row(business, r) for r in reviews)

    if not rows:
        sys.exit("\nNo reviews collected — nothing written.")
    write_csv(rows, args.out)


if __name__ == "__main__":
    main()
