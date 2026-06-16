# Export a Google Maps List to CSV with Python

Code from the tutorial: [Export Google Maps List to CSV: A Python Tutorial](https://flybyapis.com/blog/export-google-maps-list/)

Pulls a full list of businesses from any Google Maps search using the
[Google Maps Scraper API](https://flybyapis.com/apis/google-maps/) and writes
it to a CSV with names, ratings, phone numbers, websites, and addresses.

## Files

| File | What it is |
|------|-----------|
| `export.py` | The exporter: search, paginate, dedup, write CSV |
| `requirements.txt` | Python dependencies (just `requests`) |

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
export RAPIDAPI_KEY="your_key_here"
```

## Run

```bash
python export.py                              # coffee shops in Austin, 300 rows
python export.py "dentists in Chicago" 500    # custom query + target count
```

The output lands in `google_maps_list.csv`, ready to open in Excel or Google Sheets.

## How it works

1. Calls the `/locate_and_search` endpoint with a plain-English query.
2. One request returns up to 200 businesses, so it pages with `offset` until it hits your target count.
3. Dedupes by `google_id` (paginated map results overlap).
4. Flattens every field the API returns (41 columns) and writes a UTF-8 CSV. Nested
   fields like `working_hours` and `about` are kept as JSON so nothing is lost.

## Requirements

- Python 3.9+
- Free RapidAPI key: [Google Maps Extractor API on RapidAPI](https://rapidapi.com/flybyapi1/api/google-maps-extractor2) (100 requests/month free)
