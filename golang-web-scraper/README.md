# Golang Web Scraper with Colly

Code from the blog post: [Golang Web Scraper: Build One With Colly in Under 30 Minutes (2026)](https://flybyapis.com/blog/golang-web-scraper/)

A complete, runnable Go web scraper built with [Colly](https://github.com/gocolly/colly). It crawls every page of [books.toscrape.com](https://books.toscrape.com) (a sandbox built for scraping practice), extracts each book's title, price, rating and stock status, follows pagination to the end, scrapes pages concurrently, and writes everything to a CSV.

## Two approaches

### 1. DIY with Colly (`colly-scraper/`)

The full tutorial scraper: HTTP requests, CSS selectors, pagination, concurrency, CSV export, and production hardening (rate limiting, random delays, retries with backoff, rotating User-Agent, optional proxies).

```bash
go run ./colly-scraper

# Custom output file and concurrency
go run ./colly-scraper -out=mybooks.csv -parallel=4

# Route through proxies (comma-separated, with scheme)
PROXIES="http://user:pass@host:port,http://host2:port" go run ./colly-scraper
```

Scrapes all 1,000 books across 50 pages into `books.csv`.

### 2. Via FlyByAPIs API (`api-scraper/`)

When a site fights back with JavaScript rendering, CAPTCHAs, or IP bans, you stop maintaining a scraper and call a managed API instead. This example hits the [FlyByAPIs Google Search API](https://flybyapis.com/apis/google-search/) and prints the organic results.

```bash
# Get a free key at RapidAPI
export RAPIDAPI_KEY=your_key_here

go run ./api-scraper -q "golang web scraper"
go run ./api-scraper -q "best go libraries" -gl us -num 20
```

## Requirements

- Go 1.22+
- `go mod download` pulls Colly and its dependencies

## License

MIT
