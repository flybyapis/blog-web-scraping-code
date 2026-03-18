# Amazon Price Tracker with Python

Code from the tutorial: [How to Build an Amazon Price Tracker with Python](https://flybyapis.com/blog/amazon-price-tracker-python/)

Uses the [Flyby Amazon API](https://flybyapis.com/apis/amazon-scraper/) to track product prices, store history in CSV, send Telegram alerts on price drops, and generate matplotlib charts.

## Files

| File | What it is |
|------|-----------|
| `tracker.py` | Main script — continuous mode, `--once`, and `--plot` |
| `config.example.py` | Config template — copy to `config.py` and fill in your values |
| `requirements.txt` | Python dependencies |

## Setup

```bash
cp config.example.py config.py   # Fill in your API key, Telegram token, and ASINs
pip install -r requirements.txt
python tracker.py                 # Start continuous tracking
```

Other modes:

```bash
python tracker.py --once   # Check prices once and exit
python tracker.py --plot   # Generate price history chart
```

## Requirements

- Python 3.10+
- Free RapidAPI key: [Amazon Product Data API on RapidAPI](https://rapidapi.com/flybyapi1/api/real-time-amazon-data-the-most-complete)
