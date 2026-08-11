import csv
import os
import time

import requests

API_HOST = "google-maps-extractor2.p.rapidapi.com"
API_KEY = os.environ["RAPIDAPI_KEY"]  # export RAPIDAPI_KEY=... never hardcode it

QUERY = "barber shop in El Paso, TX, USA"  # your niche + city here
PAGES = 3    # 3 pages x 20 results = 60 listings checked
LIMIT = 20   # max results per request


def fetch_page(offset):
    response = requests.get(
        f"https://{API_HOST}/locate_and_search",
        headers={"x-rapidapi-host": API_HOST, "x-rapidapi-key": API_KEY},
        params={
            "query": QUERY,
            "country": "us",
            "language": "en",
            "limit": LIMIT,
            "offset": offset,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("data", [])


leads = {}
for page in range(PAGES):
    batch = fetch_page(page * LIMIT)
    if not batch:  # no more results, stop early
        break
    for biz in batch:
        if biz.get("website_url"):  # has a website: not a lead
            continue
        place_id = biz.get("place_id")
        if not place_id or place_id in leads:  # dedupe across pages
            continue
        leads[place_id] = {
            "name": biz.get("name"),
            "phone": biz.get("phone") or biz.get("full_phone") or "",
            "address": biz.get("full_address") or "",
            "category": biz.get("main_category") or "",
            "rating": biz.get("rating") or 0,
            "reviews": biz.get("reviews_count") or 0,
            "maps_link": f"https://www.google.com/maps/place/?q=place_id:{place_id}",
        }
    time.sleep(1)  # be polite between pages

rows = sorted(leads.values(), key=lambda r: r["reviews"], reverse=True)

fields = ["name", "phone", "address", "category", "rating", "reviews", "maps_link"]
with open("leads.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print(f"{len(rows)} no-website leads saved to leads.csv")
