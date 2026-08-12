# Amazon Data to a Spreadsheet: Sheets Template + Python CSV

Code for the FlyByAPIs blog post [Amazon Spreadsheet: Free Auto-Filling Template + CSV Method](https://flybyapis.com/blog/amazon-spreadsheet/).

Two ways to get live Amazon product data (prices, ratings, rankings) into a spreadsheet:

- `google-sheets-apps-script/Code.gs` — paste into a blank Google Sheet (Extensions > Apps Script). Run `setup()` once to build the template, `refreshData()` to fill it, and add a daily time-driven trigger to keep it updating itself.
- `python-csv/amazon_to_csv.py` — writes `amazon_products.csv` from one or more search queries.

Both use the [Amazon Product Data API](https://flybyapis.com/apis/amazon-scraper/) on RapidAPI.

## Setup

1. Get a free API key (100 requests/month, no credit card): [Amazon Product Data API on RapidAPI](https://rapidapi.com/flybyapi1/api/real-time-amazon-data-the-most-complete)
2. **Apps Script:** replace `PASTE_YOUR_KEY_HERE` at the top of `Code.gs`.
3. **Python:**

```bash
cd python-csv
pip install -r requirements.txt
RAPIDAPI_KEY=your_key_here python3 amazon_to_csv.py
```

## Notes

- The `marketplace` parameter selects the Amazon site (`com`, `co.uk`, `de`, `fr`, `co.jp`, ... 22 supported). Every request is routed through an IP inside that marketplace's country, so prices match what a local shopper sees.
- The Apps Script keeps the top 10 products per search so the sheet stays readable. Delete `.slice(0, 10)` to log every result (up to 48 per search).
- Rows are appended with a timestamp, so re-running builds price history for free.
