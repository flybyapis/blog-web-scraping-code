"""
Web Scraping Amazon with Python & Selenium
Blog post: https://flybyapis.com/blog/web-scraping-amazon/

Usage:
    python scraper.py                          # scrape a single product
    python scraper.py --search "headphones"    # scrape search results
"""

import argparse
import random
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]


def create_driver(proxy=None):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")

    if proxy:
        options.add_argument(f"--proxy-server={proxy}")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )
    return driver


def human_delay():
    if random.random() < 0.1:
        time.sleep(random.uniform(15, 30))
    else:
        time.sleep(random.uniform(3, 8))


def scrape_product(asin, marketplace="com"):
    driver = create_driver()
    url = f"https://www.amazon.{marketplace}/dp/{asin}"

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "productTitle"))
        )
        time.sleep(random.uniform(2, 5))

        product = {"asin": asin}

        product["title"] = driver.find_element(By.ID, "productTitle").text.strip()

        try:
            whole = driver.find_element(By.CSS_SELECTOR, "span.a-price-whole").text.replace(".", "").replace(",", "")
            fraction = driver.find_element(By.CSS_SELECTOR, "span.a-price-fraction").text
            symbol = driver.find_element(By.CSS_SELECTOR, "span.a-price-symbol").text
            product["price"] = f"{symbol}{whole}.{fraction}"
        except Exception:
            try:
                price_el = driver.find_element(
                    By.CSS_SELECTOR, "#corePriceDisplay_desktop_feature_div span.a-offscreen"
                )
                product["price"] = price_el.get_attribute("textContent").strip()
            except Exception:
                product["price"] = None

        try:
            rating_text = driver.find_element(
                By.CSS_SELECTOR, "span[data-hook='rating-out-of-text']"
            ).text
            product["rating"] = float(rating_text.split(" ")[0])
        except Exception:
            try:
                rating_el = driver.find_element(By.CSS_SELECTOR, "i.a-icon-star span.a-icon-alt")
                product["rating"] = float(rating_el.get_attribute("textContent").split(" ")[0])
            except Exception:
                product["rating"] = None

        try:
            reviews = driver.find_element(By.ID, "acrCustomerReviewText").text
            product["reviews_count"] = reviews.split(" ")[0].replace(",", "").replace("(", "").replace(")", "")
        except Exception:
            product["reviews_count"] = None

        try:
            product["availability"] = driver.find_element(
                By.ID, "availability"
            ).text.strip()
        except Exception:
            product["availability"] = None

        return product

    finally:
        driver.quit()


def scrape_search(query, marketplace="com", page=1):
    driver = create_driver()
    url = f"https://www.amazon.{marketplace}/s?k={query}&page={page}"

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[data-component-type='s-search-result']")
            )
        )
        time.sleep(random.uniform(3, 6))

        results = []
        cards = driver.find_elements(
            By.CSS_SELECTOR, "[data-component-type='s-search-result']"
        )

        for card in cards:
            product = {}
            product["asin"] = card.get_attribute("data-asin")

            try:
                product["title"] = card.find_element(By.CSS_SELECTOR, "h2 span").text.strip()
            except Exception:
                product["title"] = None

            try:
                whole = card.find_element(By.CSS_SELECTOR, "span.a-price-whole").text.replace(".", "").replace(",", "")
                fraction = card.find_element(By.CSS_SELECTOR, "span.a-price-fraction").text
                product["price"] = f"${whole}.{fraction}"
            except Exception:
                try:
                    offscreen = card.find_element(By.CSS_SELECTOR, "span.a-price span.a-offscreen")
                    product["price"] = offscreen.get_attribute("textContent").strip()
                except Exception:
                    product["price"] = None

            try:
                rating_el = card.find_element(By.CSS_SELECTOR, "span.a-icon-alt")
                product["rating"] = float(rating_el.get_attribute("textContent").split(" ")[0])
            except Exception:
                product["rating"] = None

            try:
                card.find_element(By.XPATH, ".//span[contains(text(), 'Sponsored')]")
                product["sponsored"] = True
            except Exception:
                product["sponsored"] = False

            if product["asin"]:
                results.append(product)

        return results

    finally:
        driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Amazon product data with Selenium")
    parser.add_argument("--asin", default="B09G9FPHY6", help="Product ASIN to scrape")
    parser.add_argument("--search", help="Search query (overrides --asin)")
    parser.add_argument("--marketplace", default="com", help="Amazon marketplace (com, co.uk, de, ...)")
    args = parser.parse_args()

    if args.search:
        print(f"Searching Amazon for: {args.search}")
        products = scrape_search(args.search, marketplace=args.marketplace)
        for p in products:
            print(f"  {p['asin']} | {(p['title'] or '')[:60]} | {p['price']}")
        print(f"\nFound {len(products)} products")
    else:
        print(f"Scraping product: {args.asin}")
        result = scrape_product(args.asin, marketplace=args.marketplace)
        for k, v in result.items():
            print(f"  {k}: {v}")
