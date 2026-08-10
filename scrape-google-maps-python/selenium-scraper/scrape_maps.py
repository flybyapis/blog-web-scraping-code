"""
Scrape Google Maps search results with Selenium.

Searches Google Maps for a query, scrolls the results feed until it has
enough businesses (or hits the end of the list), and writes name, rating,
review count, category, address, and link to a CSV.

Usage:
    python scrape_maps.py                          # coffee shops in Austin, 60 results
    python scrape_maps.py "dentists in Chicago" 100
"""

import csv
import re
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

FEED = 'div[role="feed"]'
CARD_LINK = 'a[href*="/maps/place/"]'
END_MARKER = "You've reached the end of the list."


def build_driver(headless: bool = True) -> webdriver.Chrome:
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1280,900")
    opts.add_argument("--lang=en-US")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)


def accept_consent(driver) -> None:
    """Click through Google's cookie consent page if it shows up (EU IPs mostly)."""
    for label in ("Accept all", "Reject all"):
        try:
            driver.find_element(By.XPATH, f'//button[.//span[text()="{label}"]]').click()
            time.sleep(2)
            return
        except NoSuchElementException:
            continue


def scroll_feed(driver, target: int, max_rounds: int = 40) -> None:
    """Scroll the results panel until we have `target` cards or hit the end."""
    feed = driver.find_element(By.CSS_SELECTOR, FEED)
    seen = 0
    stale_rounds = 0

    for _ in range(max_rounds):
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", feed)
        time.sleep(2)

        count = len(driver.find_elements(By.CSS_SELECTOR, f"{FEED} {CARD_LINK}"))
        if END_MARKER in feed.text:
            print(f"Reached the end of the list at {count} results.")
            return
        if count >= target:
            print(f"Collected {count} result cards.")
            return
        stale_rounds = stale_rounds + 1 if count == seen else 0
        if stale_rounds >= 3:
            print(f"No new results after 3 scrolls, stopping at {count}.")
            return
        seen = count
        print(f"Scrolled: {count} results loaded...")


def parse_cards(driver) -> list[dict]:
    """Extract structured data from each loaded result card."""
    rows = []
    cards = driver.find_elements(By.CSS_SELECTOR, f"{FEED} > div")

    for card in cards:
        try:
            link = card.find_element(By.CSS_SELECTOR, CARD_LINK)
        except NoSuchElementException:
            continue  # spacer divs and ads have no place link

        name = link.get_attribute("aria-label") or ""
        row = {"name": name.strip(), "url": link.get_attribute("href")}

        # The star rating lives in an aria-label like "4.5 stars"
        try:
            stars = card.find_element(By.CSS_SELECTOR, 'span[role="img"]')
            m = re.search(r"[\d.]+", stars.get_attribute("aria-label") or "")
            if m:
                row["rating"] = float(m.group())
        except NoSuchElementException:
            pass

        # The card text holds category and address on one line,
        # e.g. "Coffee shop · 507 Pressler St"
        for line in card.text.split("\n"):
            if "·" in line and "star" not in line.lower():
                parts = [p.strip(" ·,") for p in line.split("·") if p.strip(" ·,")]
                if parts and not any(ch.isdigit() for ch in parts[0]):
                    row["category"] = parts[0]
                    if len(parts) > 1:
                        row["address"] = parts[-1]
                    break

        if row["name"]:
            rows.append(row)
    return rows


def fetch_details(driver, rows: list[dict], limit: int = 10) -> None:
    """Visit each place page to add phone, website, and full address.

    This is the expensive part: one full page load per business. 100
    businesses at ~5 seconds each is 8+ minutes of browser time.
    """
    for row in rows[:limit]:
        driver.get(row["url"])
        time.sleep(4)

        fields = {
            "phone": 'button[data-item-id^="phone"]',
            "website": 'a[data-item-id="authority"]',
            "full_address": 'button[data-item-id="address"]',
        }
        for key, selector in fields.items():
            try:
                label = driver.find_element(By.CSS_SELECTOR, selector).get_attribute("aria-label") or ""
                row[key] = label.split(":", 1)[-1].strip()
            except NoSuchElementException:
                row[key] = ""
        print(f"Details: {row['name']} | {row['phone']} | {row['website']}")


def write_csv(rows: list[dict], path: str = "google_maps_results.csv") -> None:
    columns = ["name", "rating", "category", "address", "phone", "website", "full_address", "url"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {path}")


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else "coffee shops in Austin"
    target = int(sys.argv[2]) if len(sys.argv) > 2 else 60

    driver = build_driver(headless=True)
    try:
        driver.get(f"https://www.google.com/maps/search/{query.replace(' ', '+')}?hl=en")
        time.sleep(4)
        accept_consent(driver)
        scroll_feed(driver, target)
        rows = parse_cards(driver)
        fetch_details(driver, rows, limit=5)
        write_csv(rows)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
