# Amazon Price Tracker — Configuration
# Copy this file to config.py and fill in your values.

# ── API key ──────────────────────────────────────────────
# Get yours at: https://rapidapi.com/flybyapi1/api/real-time-amazon-data-the-most-complete
RAPIDAPI_KEY = "your-rapidapi-key-here"

# ── Telegram bot ─────────────────────────────────────────
# 1. Open Telegram → search @BotFather → /newbot → follow prompts
# 2. Copy the bot token below
# 3. Create a group or channel and add your bot as admin
# 4. Post a message in the group/channel
# 5. Visit https://api.telegram.org/bot<TOKEN>/getUpdates
# 6. Copy the chat id from "chat":{"id": ...} — it's a negative number like -1001234567890
TELEGRAM_BOT_TOKEN = "your-telegram-bot-token"
TELEGRAM_CHAT_ID = -1001234567890  # replace with your channel/group chat ID

# ── Products to track ────────────────────────────────────
# Format: "ASIN": {"name": "...", "target_price": X.XX, "country": "US"}
# Find the ASIN on any Amazon product URL — it's the 10-char code after /dp/
PRODUCTS = {
    "B0BJQWYLYN": {
        "name": "AirPods Pro 2",
        "target_price": 189.00,
        "country": "US",
    },
    "B09XS7JWHH": {
        "name": "Sony WH-1000XM5",
        "target_price": 248.00,
        "country": "US",
    },
}

# ── Settings ─────────────────────────────────────────────
CHECK_INTERVAL_HOURS = 6
CSV_FILE = "price_history.csv"
