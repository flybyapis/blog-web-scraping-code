# BeautifulSoup vs Scrapy — benchmark code

Code from the blog post: [BeautifulSoup vs Scrapy: When Each One Wins (With Benchmarks) (2026)](https://flybyapis.com/blog/beautifulsoup-vs-scrapy/)

Three scrapers that do the **same job** — scrape every book on
[books.toscrape.com](https://books.toscrape.com) (a sandbox built for scraping
practice): crawl all 50 listing pages, follow each book to its detail page, pull
title/price/stock, write a CSV. That's 50 + 1,000 = **1,050 requests** per run,
the exact job benchmarked in the post.

The point of the comparison isn't that one library is "better." BeautifulSoup is
a **parser**, Scrapy is a **framework**. The speed gap comes from concurrency,
not parsing — which is why a threaded BeautifulSoup script nearly catches Scrapy.

## What's here

| Folder / file | What it is |
|---------------|------------|
| `beautifulsoup-scraper/scraper.py` | BeautifulSoup + requests, **synchronous** (one request at a time — the slow column) |
| `beautifulsoup-scraper/scraper_threaded.py` | BeautifulSoup + requests, **threaded** (ThreadPoolExecutor — closes the gap) |
| `scrapy-scraper/books_spider.py` | **Scrapy** spider, async, default 16 concurrent requests |
| `scrapy-plus-bs4/parse_with_bs4.py` | Scrapy crawling + **BeautifulSoup parsing** inside the callback |
| `benchmark.py` | Runs all three and prints the comparison table |
| `api-scraper/scraper.py` | The off-ramp: structured data via the [FlyByAPIs Google Search API](https://flybyapis.com/apis/google-search/) |

## Setup

```bash
pip install -r requirements.txt
```

## Run the scrapers

```bash
# BeautifulSoup, synchronous
python beautifulsoup-scraper/scraper.py --out books.csv

# BeautifulSoup, 20 threads
python beautifulsoup-scraper/scraper_threaded.py --workers 20 --out books.csv

# Scrapy (no project needed — runs the spider file directly)
scrapy runspider scrapy-scraper/books_spider.py -o books.csv

# Scrapy + BeautifulSoup together
scrapy runspider scrapy-plus-bs4/parse_with_bs4.py -o books.csv
```

## Reproduce the benchmark

```bash
python benchmark.py
```

The numbers in the post (**105s / 14s / 11s**) came from an M2 MacBook Air over
home fiber. Yours will differ with hardware and network — but the ratios hold.

| Metric | BeautifulSoup (sync) | BeautifulSoup (20 threads) | Scrapy (async) |
|--------|----------------------|----------------------------|----------------|
| Wall-clock (1,050 pages) | ~105 s | ~14 s | ~11 s |
| Throughput | ~10 pages/s | ~75 pages/s | ~95 pages/s |
| Concurrency | none | manual (threads) | built-in |

> This hits books.toscrape.com 1,050 times per scraper. It's a sandbox made for
> this, but be reasonable and don't loop the benchmark needlessly.

## The off-ramp (when you've outgrown both)

BeautifulSoup and Scrapy stop where JavaScript rendering, proxy rotation and
anti-bot detection begin. When staying unblocked costs more than parsing, a
managed API is the better deal:

```bash
export RAPIDAPI_KEY=your_key_here   # free: https://rapidapi.com/flybyapi1/api/google-serp-search-api
python api-scraper/scraper.py -q "best python scraping library" --num 20
```

## License

MIT
