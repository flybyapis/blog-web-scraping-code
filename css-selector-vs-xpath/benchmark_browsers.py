"""CSS selector vs XPath benchmark: real browsers (Selenium + Playwright).

Serves the saved books.toscrape.com page locally, then measures two things:

1. Raw engine speed inside the browser: document.querySelectorAll(css) vs
   document.evaluate(xpath), timed in-page with performance.now() so no
   driver overhead pollutes the numbers.
2. Driver round-trip: what you actually feel in Selenium/Playwright when you
   call find_elements / query_selector_all — includes IPC overhead.

Run with --selenium, --playwright, or both.
"""

import argparse
import http.server
import json
import statistics
import threading
import time
from functools import partial
from pathlib import Path

HERE = Path(__file__).parent
PORT = 8901
URL = f"http://127.0.0.1:{PORT}/books_page.html"

PAIRS = [
    ("Product links (descendant)", "article.product_pod h3 a",
     "//article[contains(concat(' ', normalize-space(@class), ' '), ' product_pod ')]//h3//a"),
    ("Prices (class)", "p.price_color",
     "//p[contains(concat(' ', normalize-space(@class), ' '), ' price_color ')]"),
    ("In-stock labels (nested class)", "article.product_pod p.instock.availability",
     "//article[contains(concat(' ', normalize-space(@class), ' '), ' product_pod ')]"
     "//p[contains(@class, 'instock') and contains(@class, 'availability')]"),
]

IN_PAGE_JS = """
(pairs) => {
  const ITER = 2000;
  const out = [];
  for (const [label, css, xpath] of pairs) {
    const nCss = document.querySelectorAll(css).length;
    const snap = XPathResult.ORDERED_NODE_SNAPSHOT_TYPE;
    const nXp = document.evaluate(xpath, document, null, snap, null).snapshotLength;

    let t0 = performance.now();
    for (let i = 0; i < ITER; i++) document.querySelectorAll(css);
    const cssUs = (performance.now() - t0) / ITER * 1000;

    t0 = performance.now();
    for (let i = 0; i < ITER; i++)
      document.evaluate(xpath, document, null, snap, null);
    const xpUs = (performance.now() - t0) / ITER * 1000;

    out.push({label, nCss, nXp, cssUs, xpUs});
  }
  return out;
}
"""


def serve():
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE))
    httpd = http.server.HTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def roundtrip(find, n=30):
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        find()
        times.append((time.perf_counter() - t0) * 1000)
    return statistics.median(times)


def report_in_page(tool, rows):
    print(f"\n[{tool}] in-page engine speed (µs/query, 2000 iterations)")
    for r in rows:
        if r["nCss"] != r["nXp"]:
            raise SystemExit(f"MISMATCH {r['label']}: css={r['nCss']} xpath={r['nXp']}")
        print(f"  {r['label']:<38} n={r['nCss']:>2}  css={r['cssUs']:>7.1f}µ  xpath={r['xpUs']:>7.1f}µ")


def run_playwright():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL)
        rows = page.evaluate(IN_PAGE_JS, [list(t) for t in PAIRS])
        report_in_page("Playwright/Chromium", rows)

        print("\n[Playwright] driver round-trip (median ms, 30 calls)")
        for label, css, xpath in PAIRS:
            n_css = len(page.query_selector_all(css))
            n_xp = len(page.query_selector_all(f"xpath={xpath}"))
            assert n_css == n_xp, (label, n_css, n_xp)
            t_css = roundtrip(lambda: page.query_selector_all(css))
            t_xp = roundtrip(lambda: page.query_selector_all(f"xpath={xpath}"))
            print(f"  {label:<38} n={n_css:>2}  css={t_css:>6.2f}ms  xpath={t_xp:>6.2f}ms")
        browser.close()


def run_selenium():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By

    opts = Options()
    opts.add_argument("--headless=new")
    driver = webdriver.Chrome(options=opts)
    try:
        driver.get(URL)
        rows = driver.execute_script(
            f"return ({IN_PAGE_JS})(arguments[0]);", [list(t) for t in PAIRS]
        )
        report_in_page("Selenium/Chrome", rows)

        print("\n[Selenium] driver round-trip (median ms, 30 calls)")
        for label, css, xpath in PAIRS:
            n_css = len(driver.find_elements(By.CSS_SELECTOR, css))
            n_xp = len(driver.find_elements(By.XPATH, xpath))
            assert n_css == n_xp, (label, n_css, n_xp)
            t_css = roundtrip(lambda: driver.find_elements(By.CSS_SELECTOR, css))
            t_xp = roundtrip(lambda: driver.find_elements(By.XPATH, xpath))
            print(f"  {label:<38} n={n_css:>2}  css={t_css:>6.2f}ms  xpath={t_xp:>6.2f}ms")
    finally:
        driver.quit()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selenium", action="store_true")
    ap.add_argument("--playwright", action="store_true")
    args = ap.parse_args()
    if not (HERE / "books_page.html").exists():
        raise SystemExit("Run benchmark_parsers.py first to download the page.")
    httpd = serve()
    try:
        if args.playwright:
            run_playwright()
        if args.selenium:
            run_selenium()
    finally:
        httpd.shutdown()
