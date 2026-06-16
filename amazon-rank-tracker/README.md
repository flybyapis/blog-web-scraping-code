# Amazon Keyword Rank Tracker

Code from the tutorial: [Track Amazon Rankings: Free and Paid Tools That Update Daily](https://flybyapis.com/blog/track-amazon-rankings/)

A tiny, no-code-required rank tracker. Put your keywords and ASINs in a CSV, run one command, and get a `rank_history.csv` you can open in Excel or Google Sheets. Run it daily to build a history of how your Amazon search positions move.

Uses the [Flyby Amazon API](https://flybyapis.com/apis/amazon-scraper/) `/search` endpoint.

## Files

| File | What it is |
|------|-----------|
| `keywords.csv` | Your list of `keyword, asin, marketplace` — the only file you edit |
| `tracker.py` | The script — you don't need to touch it |
| `rank_history.csv` | Created on first run — your ranking history |
| `requirements.txt` | Python dependencies |

## Setup

1. Add your keywords and ASINs to `keywords.csv`:

   ```csv
   keyword,asin,marketplace
   wireless earbuds,B0BSHF7WHW,com
   yoga mat,B01LP0U5X0,com
   ```

   The ASIN is the 10-character code in any product URL after `/dp/`.
   `marketplace` is `com` for the US, `co.uk` for the UK, `de` for Germany, etc.

2. Get a free API key and set it:

   ```bash
   export RAPIDAPI_KEY=your_key_here
   ```

3. Install and run:

   ```bash
   pip install -r requirements.txt
   python tracker.py
   ```

Every run appends today's positions to `rank_history.csv`. Run it once a day
(or schedule it with cron / Task Scheduler) to track rankings over time.

## Requirements

- Python 3.10+
- Free RapidAPI key: [Amazon Product Data API on RapidAPI](https://rapidapi.com/flybyapi1/api/real-time-amazon-data-the-most-complete)
