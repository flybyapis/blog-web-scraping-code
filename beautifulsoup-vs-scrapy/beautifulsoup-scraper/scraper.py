"""
BeautifulSoup + requests scraper (synchronous).

Scrapes every book on https://books.toscrape.com — a static sandbox built for
scraping practice. Crawls all 50 listing pages, follows each book to its detail
page, and pulls title, price and stock. That's 50 + 1,000 = 1,050 requests, the
same job benchmarked in the blog post.

This is the "single-threaded" column in the benchmark: one request at a time.
It's the slowest version, and that's the point — most of the wall-clock time is
spent waiting on the network, not parsing HTML.

Run:
    python scraper.py
    python scraper.py --out books.csv
"""

import argparse
import csv
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

CATALOGUE = "https://books.toscrape.com/catalogue/"
START = CATALOGUE + "page-1.html"


def parse_listing(html):
    """Return (book_detail_urls, next_page_url_or_None) for one listing page."""
    soup = BeautifulSoup(html, "lxml")
    urls = []
    for article in soup.select("article.product_pod"):
        href = article.h3.a["href"]
        urls.append(urljoin(CATALOGUE, href))
    next_link = soup.select_one("li.next a")
    next_url = urljoin(CATALOGUE, next_link["href"]) if next_link else None
    return urls, next_url


def parse_detail(html):
    """Pull the fields we care about from a single product page."""
    soup = BeautifulSoup(html, "lxml")
    return {
        "title": soup.select_one("div.product_main h1").get_text(strip=True),
        "price": soup.select_one("p.price_color").get_text(strip=True),
        "stock": soup.select_one("p.availability").get_text(strip=True),
    }


def get_html(session, url):
    resp = session.get(url, timeout=10)
    resp.encoding = "utf-8"  # books.toscrape is utf-8; requests guesses otherwise
    return resp.text


def scrape(out_path):
    session = requests.Session()
    rows = []

    next_url = START
    while next_url:
        detail_urls, next_url = parse_listing(get_html(session, next_url))
        for url in detail_urls:
            rows.append(parse_detail(get_html(session, url)))

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "price", "stock"])
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="books.csv")
    args = parser.parse_args()

    start = time.perf_counter()
    count = scrape(args.out)
    elapsed = time.perf_counter() - start
    print(f"Scraped {count} books in {elapsed:.1f}s -> {args.out}")
