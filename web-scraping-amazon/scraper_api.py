"""
Amazon data via FlyByAPIs REST API (no Selenium needed)
Blog post: https://flybyapis.com/blog/web-scraping-amazon/

Get your free API key at:
https://rapidapi.com/flybyapi1/api/real-time-amazon-data-the-most-complete

Usage:
    python scraper_api.py                              # product details
    python scraper_api.py --search "headphones"        # search products
"""

import argparse
import os

import requests

API_KEY = os.environ.get("RAPIDAPI_KEY", "YOUR_API_KEY")
API_HOST = "real-time-amazon-data-the-most-complete.p.rapidapi.com"

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": API_HOST,
}


def get_product(asin, marketplace="com"):
    url = f"https://{API_HOST}/product-details"
    params = {"asin": asin, "marketplace": marketplace}

    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()["data"]


def search_products(query, marketplace="com", page=1):
    url = f"https://{API_HOST}/search"
    params = {"query": query, "marketplace": marketplace, "page": str(page)}

    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()["data"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Amazon data via FlyByAPIs API")
    parser.add_argument("--asin", default="B09G9FPHY6", help="Product ASIN")
    parser.add_argument("--search", help="Search query (overrides --asin)")
    parser.add_argument("--marketplace", default="com", help="Marketplace (com, co.uk, de, ...)")
    args = parser.parse_args()

    if API_KEY == "YOUR_API_KEY":
        print("Set your API key: export RAPIDAPI_KEY=your_key_here")
        print("Get one free at: https://rapidapi.com/flybyapi1/api/real-time-amazon-data-the-most-complete")
        exit(1)

    if args.search:
        print(f"Searching: {args.search}\n")
        data = search_products(args.search, marketplace=args.marketplace)
        for p in data["products"]:
            print(f"  {p['asin']} | {p['title'][:60]}")
            print(f"    Price: {p.get('price', 'N/A')} | Rating: {p.get('rating', 'N/A')} | Sponsored: {p.get('sponsored', False)}")
        print(f"\n{data.get('total_results', '?')} total results")
    else:
        print(f"Product: {args.asin}\n")
        p = get_product(args.asin, marketplace=args.marketplace)
        print(f"  Title: {p['title']}")
        buybox = p.get("buybox_seller", {})
        print(f"  Price: {buybox.get('price', 'N/A')}")
        print(f"  Rating: {p.get('rating', 'N/A')} ({p.get('reviews_count', 0)} reviews)")
        print(f"  Availability: {buybox.get('stock_status', 'N/A')}")
