# Amazon Deals Bot for Telegram

Code from the tutorial: [How to Build an Amazon Deals Bot With Telegram Alerts](https://flybyapis.com/blog/amazon-deals-bot-telegram/)

Uses the [Amazon API Scraper](https://flybyapis.com/apis/amazon-scraper/) to fetch live Amazon deals and push them to a Telegram channel — with product images, prices, and direct links.

## Files

| File | What it is |
|------|-----------|
| `amazon_deals_bot.py` | Python script — runs via cron, deduplicates via local JSON file |
| `google_sheets_script.js` | Google Apps Script — paste into Extensions > Apps Script, no server needed |

## Setup

1. Get a free API key: [Amazon Product Data API on RapidAPI](https://rapidapi.com/flybyapi1/api/real-time-amazon-data-the-most-complete)
2. Create a Telegram bot via @BotFather and get your bot token + chat ID
3. Follow the full setup guide
