# Scrape Google Maps With Python

Companion code for the FlyByAPIs blog post
[Scrape Google Maps With Python: Full Tutorial With Working Code](https://flybyapis.com/blog/scrape-google-maps-python/).

Two complete methods, same output (a CSV of businesses):

| Folder | Method | What it does |
|--------|--------|--------------|
| `selenium-scraper/` | DIY browser automation | Searches Google Maps, scrolls the results feed to beat infinite scroll, parses each card (name, rating, category, address), then visits place pages for phone + website. |
| `api-scraper/` | FlyByAPIs Google Maps Extractor API | Same data plus review counts, up to 200 businesses per request, paginated with `offset`. Includes a bonus `fetch_reviews()` for full review text. |

## Setup

```bash
pip install -r requirements.txt
```

## Run the Selenium scraper

Requires Google Chrome installed. Verified working against the live Google Maps
interface in August 2026.

```bash
cd selenium-scraper
python scrape_maps.py "coffee shops in Austin" 60
```

Writes `google_maps_results.csv` with name, rating, category, address, phone,
website, full address, and place URL. Detail lookups (phone/website) are limited
to the first 5 rows by default; raise the `limit` in `fetch_details()` if you
have time to spare (each place is a ~5 second page load).

## Run the API scraper

Get a free key (100 requests/month, no credit card) from
[the Google Maps Extractor on RapidAPI](https://rapidapi.com/flybyapi1/api/google-maps-extractor2).

```bash
export RAPIDAPI_KEY="your_key_here"
cd api-scraper
python scraper.py "coffee shops in Austin" 400
```

Writes `google_maps_results.csv` with name, rating, reviews count, category,
address, phone, website, coordinates, and Google ID.
