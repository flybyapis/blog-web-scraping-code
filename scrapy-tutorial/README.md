# How to Use Scrapy — tutorial code

Code from the blog post: [How to Use Scrapy: From Install to First Spider in 20 Minutes (2026)](https://flybyapis.com/blog/how-to-use-scrapy/)

Two spiders that take you from a blank file to real scraped data, plus the API
off-ramp for when Scrapy hits a wall (JavaScript, CAPTCHAs, anti-bot).

Both targets are official Scrapy practice sandboxes, built to be scraped:
[quotes.toscrape.com](https://quotes.toscrape.com) and
[books.toscrape.com](https://books.toscrape.com).

## What's here

| File | What it is |
|------|------------|
| `quotes_spider.py` | Your **first spider**. Pulls quote text, author, and tags off one page. The 20-minute payoff. |
| `books_spider.py` | A **real crawl**: follows every listing page, follows each book to its detail page, exports the full catalog. |
| `api-scraper/scraper.py` | The **off-ramp**: structured search data via the [FlyByAPIs Google Search API](https://flybyapis.com/apis/google-search/), no spider needed. |

## Setup

```bash
pip install -r requirements.txt
```

## Run the spiders

```bash
# First spider (no scrapy project needed, runs the file directly)
scrapy runspider quotes_spider.py -o quotes.json

# Real crawl with pagination + detail pages, export to CSV
scrapy runspider books_spider.py -o books.csv

# Same crawl, but polite (delay + auto-throttle) for real sites
scrapy runspider books_spider.py -o books.csv -s DOWNLOAD_DELAY=1 -s AUTOTHROTTLE_ENABLED=True
```

Test selectors interactively before you commit them to a spider:

```bash
scrapy shell "https://quotes.toscrape.com"
>>> response.css("span.text::text").get()
```

## The off-ramp (when you've outgrown Scrapy)

Scrapy stops exactly where JavaScript rendering, proxy rotation, and anti-bot
detection begin. When staying unblocked costs more than parsing, a managed API
is the better deal:

```bash
export RAPIDAPI_KEY=your_key_here   # free: https://rapidapi.com/flybyapi1/api/google-serp-search-api
python api-scraper/scraper.py -q "how to use scrapy" --num 20
```

## License

MIT
