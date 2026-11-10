"""CSS selector vs XPath benchmark: parsing libraries (lxml, parsel, BeautifulSoup).

Downloads one page from books.toscrape.com (a site built for scraping practice),
saves it locally, then times equivalent CSS and XPath queries against the same
parsed tree. Every query pair is verified to return the same number of elements
before timing, so we never compare selectors that do different things.
"""

import statistics
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from lxml import html as lxml_html
from lxml.cssselect import CSSSelector
from parsel import Selector

PAGE_FILE = Path(__file__).parent / "books_page.html"
ITERATIONS = 2000

# Equivalent query pairs: (label, css, xpath)
QUERIES = [
    (
        "Product links (descendant)",
        "article.product_pod h3 a",
        "//article[contains(concat(' ', normalize-space(@class), ' '), ' product_pod ')]//h3//a",
    ),
    (
        "Prices (class)",
        "p.price_color",
        "//p[contains(concat(' ', normalize-space(@class), ' '), ' price_color ')]",
    ),
    (
        "Image alt attributes",
        "article.product_pod img[alt]",
        "//article[contains(concat(' ', normalize-space(@class), ' '), ' product_pod ')]//img[@alt]",
    ),
    (
        "3rd book in each row (position)",
        "ol.row > li:nth-child(3) h3 a",
        "//ol[contains(concat(' ', normalize-space(@class), ' '), ' row ')]/li[3]//h3//a",
    ),
    (
        "In-stock labels (nested class)",
        "article.product_pod p.instock.availability",
        "//article[contains(concat(' ', normalize-space(@class), ' '), ' product_pod ')]"
        "//p[contains(@class, 'instock') and contains(@class, 'availability')]",
    ),
]


def fetch_page() -> str:
    if PAGE_FILE.exists():
        return PAGE_FILE.read_text(encoding="utf-8")
    resp = requests.get("https://books.toscrape.com/", timeout=30)
    resp.raise_for_status()
    PAGE_FILE.write_text(resp.text, encoding="utf-8")
    return resp.text


def bench(fn, iterations=ITERATIONS, repeats=5):
    """Return best-of-repeats mean microseconds per call."""
    results = []
    for _ in range(repeats):
        start = time.perf_counter()
        for _ in range(iterations):
            fn()
        elapsed = time.perf_counter() - start
        results.append(elapsed / iterations * 1_000_000)
    return min(results)


def run():
    page = fetch_page()
    tree = lxml_html.fromstring(page)
    psel = Selector(text=page)
    soup = BeautifulSoup(page, "lxml")

    print(f"page size: {len(page)} bytes, iterations: {ITERATIONS}, best of 5 runs")
    print()
    header = (
        f"{'Task':<34} {'n':>3} | {'lxml CSS':>9} {'lxml CSS*':>9} {'lxml XPath':>10} "
        f"{'parsel CSS':>10} {'parsel XPath':>12} {'BS4 CSS':>9}"
    )
    print(header)
    print("-" * len(header))

    for label, css, xpath in QUERIES:
        n_css = len(tree.cssselect(css))
        n_xp = len(tree.xpath(xpath))
        n_parsel_css = len(psel.css(css))
        n_parsel_xp = len(psel.xpath(xpath))
        n_bs4 = len(soup.select(css))
        counts = {n_css, n_xp, n_parsel_css, n_parsel_xp, n_bs4}
        if len(counts) != 1:
            raise SystemExit(
                f"MISMATCH on '{label}': lxml css={n_css} xpath={n_xp} "
                f"parsel css={n_parsel_css} xpath={n_parsel_xp} bs4={n_bs4}"
            )

        compiled_css = CSSSelector(css)  # precompiled CSS->XPath, the fair comparison
        t_lxml_css = bench(lambda: tree.cssselect(css))
        t_lxml_css_pre = bench(lambda: compiled_css(tree))
        t_lxml_xp = bench(lambda: tree.xpath(xpath))
        t_parsel_css = bench(lambda: psel.css(css))
        t_parsel_xp = bench(lambda: psel.xpath(xpath))
        t_bs4 = bench(lambda: soup.select(css), iterations=ITERATIONS // 4)

        print(
            f"{label:<34} {n_css:>3} | {t_lxml_css:>8.1f}µ {t_lxml_css_pre:>8.1f}µ "
            f"{t_lxml_xp:>9.1f}µ {t_parsel_css:>9.1f}µ {t_parsel_xp:>11.1f}µ {t_bs4:>8.1f}µ"
        )

    print()
    print("* = CSSSelector precompiled once and reused (compilation cost excluded)")
    print()
    print("CSS->XPath translation proof (what lxml/parsel actually run):")
    from cssselect import GenericTranslator

    for label, css, _ in QUERIES[:3]:
        print(f"  {css!r}")
        print(f"    -> {GenericTranslator().css_to_xpath(css)!r}")


if __name__ == "__main__":
    run()
