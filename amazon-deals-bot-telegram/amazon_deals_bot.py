import requests
import json
import os
from datetime import datetime

# === CONFIGURATION ===
RAPIDAPI_KEY = "YOUR_RAPIDAPI_KEY"
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = 123456789  # numeric ID from getUpdates — NOT "@channel_name"
SENT_DEALS_FILE = "sent_deals.json"

# === FILTERS (tweak these to your liking) ===
MARKETPLACE = "com"         # Amazon US. Change to "co.uk", "de", "es", "co.jp", etc.
LANGUAGE = "en"             # Results language
PAGE_SIZE = 30              # Deals per request (max 100)
MIN_PRICE = None            # Minimum price in USD (e.g. 20), or None to skip
MAX_PRICE = None            # Maximum price in USD (e.g. 50), or None to skip
CATEGORY = None             # Category ID number (get it from /category-list endpoint → category_node field), or None
MIN_RATING = None           # Minimum star rating (e.g. 4), or None to skip
MIN_DISCOUNT = 30           # Minimum discount % (e.g. 30)
IS_PRIME = True             # Prime-eligible deals only

# === LOAD SENT DEALS (deduplication) ===
def load_sent_deals():
    if os.path.exists(SENT_DEALS_FILE):
        with open(SENT_DEALS_FILE, "r") as f:
            return json.load(f)
    return []

def save_sent_deals(sent):
    with open(SENT_DEALS_FILE, "w") as f:
        json.dump(sent, f)

# === FETCH DEALS FROM API ===
def fetch_deals():
    url = "https://real-time-amazon-data-the-most-complete.p.rapidapi.com/deals"
    params = {
        "marketplace": MARKETPLACE,
        "language": LANGUAGE,
        "page_size": PAGE_SIZE,
        "min_discount": MIN_DISCOUNT,
        "is_prime": str(IS_PRIME).lower(),
    }
    # Optional filters — only add if set
    if MIN_PRICE is not None: params["min_price"] = MIN_PRICE
    if MAX_PRICE is not None: params["max_price"] = MAX_PRICE
    if CATEGORY is not None: params["category"] = CATEGORY
    if MIN_RATING is not None: params["min_rating"] = MIN_RATING

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "real-time-amazon-data-the-most-complete.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()["data"]["deals"]

# === SEND TELEGRAM MESSAGE WITH IMAGE ===
def send_telegram_deal(deal):
    caption = (
        f"🔥 *{deal['title']}*\n\n"
        f"💰 Was {deal.get('original_price', 'N/A')} → "
        f"Now *{deal['price_symbol']}{deal['price']}* ({deal['discount_percentage']}% off)\n\n"
        f"🔗 [See deal on Amazon]({deal['product_url']})"
    )

    image_url = deal.get("image", "")
    if image_url:
        # Download image locally — Amazon CDN blocks Telegram's servers
        img_response = requests.get(image_url, timeout=10)
        if img_response.ok:
            tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            response = requests.post(tg_url, data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption,
                "parse_mode": "Markdown"
            }, files={"photo": ("deal.jpg", img_response.content, "image/jpeg")})
            return response.ok

    # Fallback: text-only message if no image or download failed
    tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(tg_url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": caption,
        "parse_mode": "Markdown"
    })
    return response.ok

# === MAIN ===
def main():
    print(f"[{datetime.now()}] Fetching Amazon deals...")
    deals = fetch_deals()
    sent_deals = load_sent_deals()

    new_count = 0
    for deal in deals:
        deal_id = deal.get("deal_id", deal.get("asin"))
        if deal_id in sent_deals:
            continue

        if send_telegram_deal(deal):
            sent_deals.append(deal_id)
            new_count += 1
            print(f"  Sent: {deal['title'][:60]}...")

    save_sent_deals(sent_deals)
    print(f"[{datetime.now()}] Done. Sent {new_count} new deals.")

if __name__ == "__main__":
    main()
