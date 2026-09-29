# CSS Selector vs XPath — Benchmarks

Benchmark code for the blog post [CSS Selector vs XPath: The Definitive Cheat Sheet (With Real Benchmarks)](https://flybyapis.com/blog/css-selector-vs-xpath/).

Two scripts, both timing equivalent CSS and XPath queries against the same page (the [books.toscrape.com](https://books.toscrape.com/) homepage, downloaded once and cached locally). Every CSS/XPath pair is verified to return identical element counts before timing.

## What gets measured

- `benchmark_parsers.py` — lxml (CSS, precompiled CSS, XPath), parsel/Scrapy (CSS, XPath), and BeautifulSoup (CSS via soupsieve). Also prints the XPath that `cssselect` compiles each CSS selector into, which is what lxml and Scrapy actually execute.
- `benchmark_browsers.py` — Selenium/Chrome and Playwright/Chromium. Measures both the raw in-page engine speed (`querySelectorAll` vs `document.evaluate`, timed with `performance.now()`) and the full driver round-trip your script actually experiences.

## Run it

```bash
pip install -r requirements.txt
playwright install chromium   # only needed for the Playwright benchmark

python benchmark_parsers.py
python benchmark_browsers.py --playwright
python benchmark_browsers.py --selenium   # needs Chrome installed
```

Run `benchmark_parsers.py` first: it downloads and caches the test page the browser benchmark serves locally.

## Headline results (Apple Silicon, Python 3.13)

- In browser engines, CSS won every test by 4 to 40x, but the driver round-trip (4 to 16 ms) dwarfs the query cost either way.
- In lxml, hand-written XPath won 3 of 5 tasks: CSS is compiled to XPath there, so the translation layer is pure overhead.
- BeautifulSoup ran 6 to 124x slower than the equivalent lxml/parsel query and supports no XPath at all.

Your absolute numbers will differ by machine; the conclusions should hold.

Skip selector maintenance entirely for hostile targets with the [FlyByAPIs Amazon Product Data API](https://flybyapis.com/apis/amazon-scraper/).
