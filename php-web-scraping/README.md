# PHP Web Scraping: From First Request to Full Crawler

Code from the blog post: [PHP Web Scraping Tutorial: From First Request to Full Crawler (2026)](https://flybyapis.com/blog/php-web-scraping-tutorial/)

A complete, runnable PHP crawler built with [Guzzle](https://docs.guzzlephp.org/) and [Symfony DomCrawler](https://symfony.com/doc/current/components/dom_crawler.html). It crawls [books.toscrape.com](https://books.toscrape.com) (a sandbox built for scraping practice) and includes everything a real crawler needs, not just a pagination loop: a link frontier with deduplication, concurrent fetching, retries with exponential backoff, selector-drift validation, and SQLite storage.

## Setup

```bash
composer install
```

Requires PHP 8.1+ with the `curl` and `pdo_sqlite` extensions (both standard).

## Two approaches

### 1. DIY crawler (`crawler.php`)

The full tutorial crawler: HTTP via Guzzle, CSS-selector parsing with DomCrawler, a breadth-first link frontier with URL dedup and a depth limit, concurrent fetching with Guzzle's `Pool`, retries with exponential backoff, per-record validation, and SQLite storage with optional CSV export.

```bash
# Crawl the whole sandbox into crawl.db
php crawler.php

# Tune it
php crawler.php --seed=https://books.toscrape.com/ --concurrency=5 --max-pages=200 --max-depth=6

# Crawl, then export the SQLite table to CSV
php crawler.php --export=books.csv
```

It writes to `crawl.db` (SQLite). The `url` primary key means re-running updates rows instead of duplicating them, so you can stop and resume.

### 2. Via the FlyByAPIs API (`api-scraper.php`)

When a site fights back with JavaScript rendering, CAPTCHAs, or IP bans, you stop maintaining a scraper and call a managed API instead. This example hits the [FlyByAPIs Google Search API](https://flybyapis.com/apis/google-search/) and prints the organic results. It is the same Guzzle client as the crawler.

```bash
# Get a free key (200 requests/month, no card) at RapidAPI:
#   https://rapidapi.com/flybyapi1/api/google-serp-search-api
export RAPIDAPI_KEY=your_key_here

php api-scraper.php "php web scraping"
php api-scraper.php "best php libraries" --num=20 --gl=us --hl=en
```

## JavaScript-rendered pages

For pages that build their content with JavaScript, the tutorial uses [Symfony Panther](https://github.com/symfony/panther) (a real Chrome driver). It is listed under `require-dev` in `composer.json`. Install Chrome/Chromium and a matching chromedriver, then `composer install` pulls Panther in. See the blog post for the runnable Panther example.

## License

MIT
