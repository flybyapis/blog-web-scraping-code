# Find Local Businesses Without Websites (Lead Gen)

Code from the tutorial: [Find Local Businesses Without Websites: Free Lead Gen Goldmine](https://flybyapis.com/blog/local-businesses-without-websites/)

Builds a web-design lead list from any Google Maps search using the
[Google Maps Scraper API](https://flybyapis.com/apis/google-maps/): every
business whose listing has no `website_url` is a prospect. Two versions,
one for Python and one for Google Sheets (no code skills needed).

## Files

| File | What it is |
|------|-----------|
| `find_leads.py` | Python version: search, paginate, filter no-website listings, write sorted `leads.csv` |
| `google_sheets_script.js` | Google Apps Script version: same logic, writes leads into the active sheet |
| `requirements.txt` | Python dependencies (just `requests`) |

## Python version

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
export RAPIDAPI_KEY="your_key_here"
python find_leads.py
```

Edit `QUERY` and `PAGES` at the top of the script to change niche, city, and depth.
Output: `leads.csv` sorted by review count descending (most established leads first).

## Google Sheets version

1. Open a new sheet (sheets.new) → Extensions → Apps Script
2. Paste `google_sheets_script.js`, set `RAPIDAPI_KEY` and `QUERY`
3. Run `findLeads` and authorize when prompted
4. Leads appear in the sheet, sorted by review count

Full step-by-step with screenshots in the
[blog post](https://flybyapis.com/blog/local-businesses-without-websites/).

## Get an API key

Free tier: 200 requests/month, each request checks 20 listings.
Sign up at [Google Maps Extractor on RapidAPI](https://rapidapi.com/flybyapi1/api/google-maps-extractor2).
