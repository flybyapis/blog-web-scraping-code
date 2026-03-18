"""
Amazon Price Tracker — FlyByAPIs

Tracks Amazon product prices via the FlyByAPIs Amazon Product Data API,
stores history in CSV, sends Telegram alerts on price drops, and generates
matplotlib price charts.

Usage:
    python tracker.py          # Start continuous tracking
    python tracker.py --once   # Check prices once and exit
    python tracker.py --plot   # Generate price history chart
"""

import csv
import json
import os
import sys
import time
from datetime import datetime, timedelta

import requests
import schedule

try:
    import config
except ImportError:
    print("Missing config.py — copy config.example.py to config.py and fill in your values.")
    sys.exit(1)


# ── Amazon API ───────────────────────────────────────────

API_URL = "https://real-time-amazon-data-the-most-complete.p.rapidapi.com/product-details"


def fetch_price(asin: str, country: str = "US") -> dict | None:
    """Fetch current price for an ASIN from the FlyByAPIs Amazon API."""
    headers = {
        "x-rapidapi-host": "real-time-amazon-data-the-most-complete.p.rapidapi.com",
        "x-rapidapi-key": config.RAPIDAPI_KEY,
    }
    params = {"asin": asin, "country": country}

    try:
        resp = requests.get(API_URL, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        product = data.get("data", {})

        raw_price = product.get("price")
        if not raw_price:
            return None

        price = float(str(raw_price).replace("$", "").replace("€", "").replace("£", "").replace("¥", "").replace("₹", "").replace(",", "").strip())

        return {
            "asin": asin,
            "title": product.get("title", "Unknown"),
            "price": price,
            "currency": product.get("price_symbol", "USD"),
            "original_price": "",
            "country": country,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        print(f"  [ERROR] Failed to fetch {asin}: {e}")
        return None


# ── CSV storage ──────────────────────────────────────────

FIELDS = ["asin", "title", "price", "currency", "original_price", "country", "timestamp"]


def save_price(record: dict):
    """Append a price record to the CSV file."""
    file_exists = os.path.exists(config.CSV_FILE)
    with open(config.CSV_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)


def load_history(asin: str) -> list[dict]:
    """Load all price records for a given ASIN."""
    if not os.path.exists(config.CSV_FILE):
        return []
    records = []
    with open(config.CSV_FILE, "r") as f:
        for row in csv.DictReader(f):
            if row["asin"] == asin:
                row["price"] = float(row["price"])
                records.append(row)
    return records


def get_lowest_price(asin: str) -> float | None:
    """Return the historical lowest price for an ASIN, or None if no data."""
    history = load_history(asin)
    if not history:
        return None
    return min(r["price"] for r in history)


# ── Alert cooldown ───────────────────────────────────────

ALERT_LOG = "alert_log.json"


def load_alert_log() -> dict:
    if not os.path.exists(ALERT_LOG):
        return {}
    with open(ALERT_LOG, "r") as f:
        return json.load(f)


def save_alert_log(log: dict):
    with open(ALERT_LOG, "w") as f:
        json.dump(log, f, indent=2)


def already_alerted(asin: str, days: int = 30) -> bool:
    log = load_alert_log()
    if asin not in log:
        return False
    last = datetime.fromisoformat(log[asin])
    return datetime.now() - last < timedelta(days=days)


def mark_alerted(asin: str):
    log = load_alert_log()
    log[asin] = datetime.now().isoformat()
    save_alert_log(log)


# ── Telegram alerts ───────────────────────────────────────


def send_telegram(message: str):
    """Send a message via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        print("  [TELEGRAM] Alert sent.")
    except Exception as e:
        print(f"  [ERROR] Telegram failed: {e}")


def check_and_alert(record: dict, target_price: float):
    """Send a Telegram alert if price is at or below target, or a new all-time low.
    Skips the alert if one was already sent for this product within the last 30 days."""
    if already_alerted(record["asin"]):
        return

    current = record["price"]
    lowest = get_lowest_price(record["asin"])
    name = config.PRODUCTS[record["asin"]]["name"]

    lines = []

    if current <= target_price:
        lines.append("\U0001f525 <b>Price drop alert!</b>")
        lines.append(f"<b>{name}</b> is now <b>${current:.2f}</b>")
        lines.append(f"Your target was: ${target_price:.2f}")

    if lowest and current < lowest:
        lines.append(f"\U0001f4c9 New all-time low! Previous: ${lowest:.2f}")

    if lines:
        lines.append(f"\nhttps://www.amazon.com/dp/{record['asin']}")
        send_telegram("\n".join(lines))
        mark_alerted(record["asin"])


# ── Price chart ──────────────────────────────────────────


def plot_prices():
    """Generate a price history chart for all tracked products."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        print("matplotlib not installed. Run: pip install matplotlib")
        return

    fig, ax = plt.subplots(figsize=(10, 5))

    for asin, info in config.PRODUCTS.items():
        history = load_history(asin)
        if not history:
            continue

        dates = [datetime.fromisoformat(r["timestamp"]) for r in history]
        prices = [r["price"] for r in history]

        ax.plot(dates, prices, marker="o", markersize=4, label=info["name"])
        ax.axhline(y=info["target_price"], linestyle="--", alpha=0.4)

    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")
    ax.set_title("Amazon Price Tracker")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    chart_path = "price_chart.png"
    fig.savefig(chart_path, dpi=150)
    print(f"[CHART] Saved to {chart_path}")
    plt.show()


# ── Main ─────────────────────────────────────────────────


def check_all():
    """Check prices for all configured products."""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Checking prices...")

    for asin, info in config.PRODUCTS.items():
        record = fetch_price(asin, info["country"])
        if not record:
            print(f"  {info['name']}: failed to fetch")
            continue

        save_price(record)
        lowest = get_lowest_price(asin)
        low_str = f"${lowest:.2f}" if lowest else "n/a"
        print(f"  {info['name']}: ${record['price']:.2f} (target: ${info['target_price']:.2f}, lowest: {low_str})")

        check_and_alert(record, info["target_price"])

    print("[DONE]")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--plot":
        plot_prices()
    elif len(sys.argv) > 1 and sys.argv[1] == "--once":
        check_all()
    else:
        print(f"Amazon Price Tracker")
        print(f"Tracking {len(config.PRODUCTS)} products every {config.CHECK_INTERVAL_HOURS}h")
        print("Press Ctrl+C to stop.\n")

        check_all()
        schedule.every(config.CHECK_INTERVAL_HOURS).hours.do(check_all)

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\nStopped.")
