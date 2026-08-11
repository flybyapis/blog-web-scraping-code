"""
The off-ramp: structured search data via the FlyByAPIs Google Search API.

Scrapy is great until a target renders in JavaScript or fights back with
CAPTCHAs and anti-bot detection. Google is the worst case: a raw spider gets
blocked in minutes. When staying unblocked costs more than parsing, you call a
managed API instead of maintaining a scraper.

This hits the FlyByAPIs Google Search API and prints the organic results. No
spider, no proxies, no headless browser.

Blog post: https://flybyapis.com/blog/how-to-use-scrapy/
Get a free key (100 requests/month): https://rapidapi.com/flybyapi1/api/google-serp-search-api

Usage:
    export RAPIDAPI_KEY=your_key_here
    python scraper.py -q "best python scraping library"
    python scraper.py -q "how to use scrapy" --gl us --num 20
"""

import argparse
import os

import requests

API_HOST = "google-serp-search-api.p.rapidapi.com"
API_KEY = os.environ.get("RAPIDAPI_KEY", "YOUR_API_KEY")

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": API_HOST,
}


def search(query, gl="us", num=10):
    url = f"https://{API_HOST}/search"
    params = {"q": query, "gl": gl, "num": str(num)}
    response = requests.get(url, headers=HEADERS, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Google search via the FlyByAPIs API")
    parser.add_argument("-q", "--query", required=True)
    parser.add_argument("--gl", default="us", help="Country code (us, gb, de, ...)")
    parser.add_argument("--num", type=int, default=10)
    args = parser.parse_args()

    if API_KEY == "YOUR_API_KEY":
        print("Set your API key: export RAPIDAPI_KEY=your_key_here")
        print("Get one free at: https://rapidapi.com/flybyapi1/api/google-serp-search-api")
        raise SystemExit(1)

    try:
        data = search(args.query, gl=args.gl, num=args.num)
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code
        raise SystemExit(f"API returned HTTP {code}. If it's a 5xx, the endpoint is busy, try again in a moment.")
    except requests.exceptions.RequestException as e:
        raise SystemExit(f"Request failed: {e}")

    results = data.get("organic_results") or data.get("results") or []
    print(f"Query: {args.query}\n")
    if not results:
        print("No organic results in the response. Raw payload:")
        print(data)
        raise SystemExit(0)
    for i, item in enumerate(results, 1):
        title = item.get("title", "")
        link = item.get("link") or item.get("url", "")
        print(f"{i:>2}. {title}")
        print(f"    {link}")
