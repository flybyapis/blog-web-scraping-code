# Web Scraping Code for blog examples

Code examples and scripts from the [FlyByAPIs blog](https://flybyapis.com/blog/) — practical web scraping tutorials using Python and the FlyByAPIs suite of data extraction APIs.

## About

Each folder in this repo corresponds to a blog post. You'll find ready-to-run scripts that demo how to use FlyByAPIs endpoints for real-world tasks: price tracking, deal bots, SERP analysis, and more.

## Articles & Code

| Folder | Article | APIs Used |
|--------|---------|-----------|
| `amazon-price-tracker-python/` | [Build an Amazon Price Tracker with Python](https://flybyapis.com/blog/amazon-price-tracker-python/) | [Amazon Product Data API](https://flybyapis.com/apis/amazon-scraper/) |
| `amazon-deals-bot-telegram/` | [Build an Amazon Deals Bot for Telegram](https://flybyapis.com/blog/amazon-deals-bot-telegram/) | [Amazon Product Data API](https://flybyapis.com/apis/amazon-scraper/) |
| `golang-web-scraper/` | [Golang Web Scraper: Build One With Colly in Under 30 Minutes](https://flybyapis.com/blog/golang-web-scraper/) | [Google Search API](https://flybyapis.com/apis/google-search/) |

## Getting Started

1. Clone the repo:
   ```bash
   git clone https://github.com/flybyapis/blog-web-scraping-code.git
   cd blog-web-scraping-code
   ```

2. Get a free API key at [RapidAPI](https://rapidapi.com/flybyapi1/api/real-time-amazon-data-the-most-complete) and set it as an environment variable:
   ```bash
   export RAPIDAPI_KEY=your_key_here
   ```

3. Navigate to any article folder and follow its own `README.md` for setup instructions.

## APIs

All examples use [FlyByAPIs](https://flybyapis.com) — a set of fast, affordable web data extraction APIs available on RapidAPI:

- [Amazon Data API](https://rapidapi.com/flybyapi1/api/real-time-amazon-data-the-most-complete)
- [Google Search API](https://rapidapi.com/flybyapi1/api/google-serp-search-api)
- [Google Maps API](https://rapidapi.com/flybyapi1/api/google-maps-extractor2)
- [AI Translator API](https://rapidapi.com/flybyapi1/api/multi-format-ai-translator-the-most-complete)

## License

MIT
