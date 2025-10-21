# -*- coding: utf-8 -*-
import os
import requests
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import feedparser

# --- 0. Load environment variables ---
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print("TOKEN:", TELEGRAM_TOKEN)
print("CHAT_ID:", CHAT_ID)

# --- 1. Initialize OpenAI client ---
client = OpenAI(api_key=OPENAI_API_KEY)

# --- 2. Weather in Kyiv ---
def get_weather():
    try:
        # English format
        url = "https://wttr.in/Kyiv?format=%C+%t&lang=en"
        return requests.get(url, timeout=5).text.strip()
    except Exception as e:
        print("Weather error:", e)
        return "Could not get weather."

# --- 3. Crypto prices ---
def get_crypto():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,mina-protocol&vs_currencies=usd"
        data = requests.get(url, timeout=10).json()
        btc = data["bitcoin"]["usd"]
        eth = data["ethereum"]["usd"]
        mina = data["mina-protocol"]["usd"]
        return f"Crypto prices:\nBTC: ${btc}\nETH: ${eth}\nMINA: ${mina}"
    except Exception as e:
        print("Crypto error:", e)
        return "Could not get crypto prices."

# --- 4. Currency rates (to UAH) ---
def get_currency():
    try:
        mono = requests.get("https://api.monobank.ua/bank/currency", timeout=5).json()
        usd = next((x for x in mono if x["currencyCodeA"] == 840 and x["currencyCodeB"] == 980), None)
        eur = next((x for x in mono if x["currencyCodeA"] == 978 and x["currencyCodeB"] == 980), None)
        return f"Currency rates:\nUSD: {usd['rateBuy']:.2f}/{usd['rateSell']:.2f}\nEUR: {eur['rateBuy']:.2f}/{eur['rateSell']:.2f}"
    except Exception as e:
        print("Currency error:", e)
        return "Could not get currency rates."

# --- 5. Latest news ---
def get_news():
    try:
        feed = feedparser.parse("https://news.google.com/rss?hl=en&gl=US&ceid=US:en")
        articles = [entry.title for entry in feed.entries[:3]]
        return "\n• " + "\n• ".join(articles)
    except Exception as e:
        print("News error:", e)
        return "No news available."

# --- 6. Fact of the day in history ---
def get_fact():
    try:
        today = datetime.now()
        url = f"http://history.muffinlabs.com/date/{today.month}/{today.day}"
        data = requests.get(url, timeout=10).json()
        events = data.get("data", {}).get("Events", [])
        if events:
            event = events[0]  # take the first event
            return f"{event['year']}: {event['text']}"
        return "Fact not found."
    except Exception as e:
        print("Fact error:", e)
        return "Could not get fact."

# --- 7. Create digest message ---
def create_digest():
    now = datetime.now()
    raw_info = f"""📅 {now.strftime('%A, %d %B %Y, %H:%M')}
☀️ Weather in Kyiv: {get_weather()}
💵 {get_currency()}
💰 {get_crypto()}
📰 News:{get_news()}
💡 Fact of the day: {get_fact()}""".strip()

    # Compress text via OpenAI for a nice structured Telegram post
    try:
        prompt = f"Create a short, structured, and informative Telegram post in English based on this text:\n{raw_info}"
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI error:", e)
        return raw_info

# --- 8. Send message to Telegram ---
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, data=json.dumps(data), headers=headers)
        print("Status code:", resp.status_code)
        print("API response:", resp.text)
    except Exception as e:
        print("Telegram send error:", e)

# --- 9. Main ---
if __name__ == "__main__":
    digest = create_digest()
    send_telegram(digest)
