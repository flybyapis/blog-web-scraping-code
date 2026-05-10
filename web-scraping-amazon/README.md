# Web Scraping Amazon with Python

Code from the blog post: [Web Scraping Amazon with Python: Selenium Guide (2026)](https://flybyapis.com/blog/web-scraping-amazon/)

## Two approaches

### 1. DIY with Selenium (`scraper.py`)

Scrapes Amazon directly using Selenium + ChromeDriver. Handles anti-detection basics (user agent rotation, webdriver flag removal, random delays).

```bash
pip install -r requirements.txt

# Scrape a single product
python scraper.py --asin B09G9FPHY6

# Search products
python scraper.py --search "wireless headphones"

# Different marketplace
python scraper.py --search "laptop" --marketplace de
```

### 2. Via FlyByAPIs API (`scraper_api.py`)

Same data, no Selenium needed. Returns structured JSON with no proxy/anti-bot headaches.

```bash
pip install requests

# Set your API key (get one free at RapidAPI)
export RAPIDAPI_KEY=your_key_here

# Product details
python scraper_api.py --asin B09G9FPHY6

# Search
python scraper_api.py --search "wireless headphones"
```

Get your free API key: https://rapidapi.com/flybyapi1/api/real-time-amazon-data-the-most-complete
