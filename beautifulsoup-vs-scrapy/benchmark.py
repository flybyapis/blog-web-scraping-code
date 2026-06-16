"""
Reproduce the benchmark from the blog post.

Runs the same 1,050-request job three ways and prints a comparison table:
  1. BeautifulSoup + requests, synchronous
  2. BeautifulSoup + requests, threaded (20 workers)
  3. Scrapy, async (default 16 concurrent requests)

The numbers in the post (105s / 14s / 11s) came from a run on an M2 MacBook Air
over home fiber. Yours will differ with hardware and network, but the ratios
hold: the synchronous version is far slower because it waits on the network one
request at a time, not because BeautifulSoup parses slowly.

Run:
    python benchmark.py

Note: this hits books.toscrape.com 1,050 times per scraper (3,150 total). It's a
sandbox built for exactly this, but be reasonable and don't loop it needlessly.
"""

import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent


def time_python(label, script, *args):
    start = time.perf_counter()
    subprocess.run([sys.executable, str(script), *args], check=True)
    return label, time.perf_counter() - start


def time_scrapy(label, spider, out):
    start = time.perf_counter()
    subprocess.run(
        ["scrapy", "runspider", str(spider), "-o", out, "--nolog"],
        check=True,
    )
    return label, time.perf_counter() - start


def main():
    results = []

    results.append(time_python(
        "BeautifulSoup (sync)",
        HERE / "beautifulsoup-scraper" / "scraper.py",
        "--out", "bench_bs4_sync.csv",
    ))

    results.append(time_python(
        "BeautifulSoup (20 threads)",
        HERE / "beautifulsoup-scraper" / "scraper_threaded.py",
        "--out", "bench_bs4_threaded.csv", "--workers", "20",
    ))

    results.append(time_scrapy(
        "Scrapy (async)",
        HERE / "scrapy-scraper" / "books_spider.py",
        "bench_scrapy.csv",
    ))

    width = max(len(label) for label, _ in results)
    print("\n" + "=" * (width + 14))
    print(f"{'Scraper'.ljust(width)}   Wall-clock")
    print("-" * (width + 14))
    for label, elapsed in results:
        print(f"{label.ljust(width)}   {elapsed:6.1f}s")
    print("=" * (width + 14))


if __name__ == "__main__":
    main()
