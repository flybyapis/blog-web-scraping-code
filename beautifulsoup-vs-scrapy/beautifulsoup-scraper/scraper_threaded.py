"""
BeautifulSoup + requests scraper (threaded).

Same job as scraper.py, but the 1,000 detail-page requests run through a
ThreadPoolExecutor instead of one at a time. This is the "20 threads" column in
the benchmark — it closes most of the gap to Scrapy because the bottleneck was
never parsing, it was waiting on the network.

The lesson from the post: "Is Scrapy faster?" really means "does it do
concurrency for me?" Here you wire concurrency up by hand. Scrapy gives it to
you for free.

Run:
    python scraper_threaded.py
    python scraper_threaded.py --workers 20 --out books.csv
"""

import argparse
import csv
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

CATALOGUE = "https://books.toscrape.com/catalogue/"
START = CATALOGUE + "page-1.html"

session = requests.Session()


def get_html(url):
    resp = session.get(url, timeout=10)
    resp.encoding = "utf-8"  # books.toscrape is utf-8; requests guesses otherwise
    return resp.text


def all_detail_urls():
    """Walk the listing pages first to collect every book's detail URL."""
    urls = []
    next_url = START
    while next_url:
        soup = BeautifulSoup(get_html(next_url), "lxml")
        for article in soup.select("article.product_pod"):
            urls.append(urljoin(CATALOGUE, article.h3.a["href"]))
        next_link = soup.select_one("li.next a")
        next_url = urljoin(CATALOGUE, next_link["href"]) if next_link else None
    return urls


def fetch_book(url):
    soup = BeautifulSoup(get_html(url), "lxml")
    return {
        "title": soup.select_one("div.product_main h1").get_text(strip=True),
        "price": soup.select_one("p.price_color").get_text(strip=True),
        "stock": soup.select_one("p.availability").get_text(strip=True),
    }


def scrape(out_path, workers):
    urls = all_detail_urls()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(fetch_book, urls))

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "price", "stock"])
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="books.csv")
    parser.add_argument("--workers", type=int, default=20)
    args = parser.parse_args()

    start = time.perf_counter()
    count = scrape(args.out, args.workers)
    elapsed = time.perf_counter() - start
    print(f"Scraped {count} books in {elapsed:.1f}s "
          f"({args.workers} threads) -> {args.out}")
