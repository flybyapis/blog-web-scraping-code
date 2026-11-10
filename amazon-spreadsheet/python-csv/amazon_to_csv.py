"""Fetch Amazon product data via the FlyByAPIs Amazon API and write it to a CSV.

Companion code for https://flybyapis.com/blog/amazon-spreadsheet/
Get a free key (100 requests/month):
https://rapidapi.com/flybyapi1/api/real-time-amazon-data-the-most-complete
"""

import csv
import os

import requests

API_KEY = os.environ.get("RAPIDAPI_KEY", "PASTE_YOUR_KEY_HERE")
HOST = "real-time-amazon-data-the-most-complete.p.rapidapi.com"

QUERIES = ["wireless earbuds", "yoga mat"]
MARKETPLACE = "com"

FIELDS = ["query", "asin", "title", "price", "original_price",
          "rating", "reviews_count", "best_seller", "position", "url"]

def search(query: str) -> list[dict]:
    resp = requests.get(
        f"https://{HOST}/search",
        headers={"x-rapidapi-key": API_KEY, "x-rapidapi-host": HOST},
        params={"query": query, "marketplace": MARKETPLACE},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"]["products"]

with open("amazon_products.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
    writer.writeheader()
    for q in QUERIES:
        for product in search(q):
            writer.writerow({"query": q, **product})
    print("Done: amazon_products.csv")
