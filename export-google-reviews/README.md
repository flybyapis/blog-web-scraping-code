# Export Google Reviews to CSV

Code from the tutorial: [How to Export Google Reviews to CSV (2 Methods That Actually Work)](https://flybyapis.com/blog/export-google-reviews/)

Pulls the full review history for any business on Google Maps using the
[Google Maps Scraper API](https://flybyapis.com/apis/google-maps/) and writes it to a CSV
with real dates, ratings, review text, reviewer details, and owner responses.

You don't need to own the business profile, so this works for clients, prospects, and
competitors — not just your own listings.

## Files

| File | What it is |
|------|-----------|
| `export_reviews.py` | Python exporter: resolve business, paginate reviews, write CSV |
| `Code.gs` | Google Apps Script: same job, straight into a spreadsheet |
| `requirements.txt` | Python dependencies (just `requests`) |

## Method 1 — Google Sheets (no install)

1. Open a new spreadsheet, then **Extensions > Apps Script**.
2. Delete the empty function, paste all of `Code.gs`.
3. Set `RAPIDAPI_KEY`, `BUSINESS`, and `MAX_REVIEWS` at the top.
4. Click **Run** and approve the permission prompt the first time.

The reviews land in the active sheet with a frozen, bold header row.

## Method 2 — Python

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
export RAPIDAPI_KEY="your_key_here"
```

```bash
# one business
python export_reviews.py "Reading Terminal Market, Philadelphia"

# more reviews, oldest-first sort, custom output file
python export_reviews.py "Zahav, Philadelphia" --max 200 --sort ratingLowToHigh --out zahav.csv

# a whole client list, one business per line
python export_reviews.py --from-file businesses.txt --out client_reviews.csv
```

| Flag | Default | What it does |
|------|---------|--------------|
| `--max` | `100` | Max reviews per business |
| `--sort` | `mostRecent` | `mostRecent`, `qualityScore`, `ratingHighToLow`, `ratingLowToHigh` |
| `--out` | `google_reviews.csv` | Output path |
| `--from-file` | — | Text file with one business per line |

## How it works

1. `/locate_and_search` turns a plain-English name like `"Zahav, Philadelphia"` into the
   `google_id` the reviews endpoint needs. Always include the city — bare names are ambiguous.
2. `/business_reviews` returns reviews for that `google_id`. **The `limit` parameter caps at 20**
   no matter what you pass, so both scripts loop on the `next_token` → `next_page_token`
   pagination until they hit your target.
3. Each review's `timestamp` (Unix epoch) becomes a real date. The API also returns `time` as a
   relative string like `"3 months ago"`, which is what most scrapers and extensions give you and
   what makes their exports impossible to sort or chart.

## Notes from testing

- Between a third and a half of reviews have a star rating but **no text** (30–48% across the
  three businesses tested) — that's normal on Google, not a bug in the export.
- `sort_by=mostRecent` orders reliably page to page, but an occasional much older review appears
  in the middle. Those are edited reviews: Google reorders them by edit date while the timestamp
  stays original.
- A business name with no match returns an empty result rather than an error, so both scripts
  skip it and carry on with the rest of the list.
- Each page of 20 reviews costs 1 API request. The free RapidAPI tier is 100 requests/month,
  which is about 2,000 reviews.

## API key

Get a free key (100 requests/month) at
[RapidAPI](https://rapidapi.com/flybyapi1/api/google-maps-extractor2). Keep it in an environment
variable for the Python script. For Apps Script the key lives in the file, so don't share that
spreadsheet publicly with edit access — and regenerate the key on RapidAPI if it ever leaks.
