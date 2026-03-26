# -*- coding: utf-8 -*-
import os
import requests
import json
import random
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
    # Try primary source: wttr.in
    try:
        url = "https://wttr.in/Kyiv?format=%C+%t&lang=en"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        print("Weather error (wttr.in):", e)
    
    # Fallback to Open-Meteo API
    try:
        # Kyiv coordinates: 50.4501, 30.5234
        url = "https://api.open-meteo.com/v1/forecast?latitude=50.45&longitude=30.52&current_weather=true&temperature_unit=celsius"
        data = requests.get(url, timeout=5).json()
        temp = data["current_weather"]["temperature"]
        weather_code = data["current_weather"]["weathercode"]
        
        # Simple weather code mapping
        weather_desc = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Foggy", 51: "Light drizzle", 61: "Light rain",
            63: "Moderate rain", 65: "Heavy rain", 71: "Light snow", 73: "Moderate snow",
            75: "Heavy snow", 95: "Thunderstorm"
        }
        desc = weather_desc.get(weather_code, "Unknown")
        return f"{desc} +{temp}°C" if temp >= 0 else f"{desc} {temp}°C"
    except Exception as e:
        print("Weather error (Open-Meteo):", e)
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

# --- 6. Daily Stoic quote ---
def get_stoic_quote():
    # Try to get quote from API
    try:
        # Quotable API with stoic philosophers
        stoic_authors = "marcus-aurelius|epictetus|seneca"
        url = f"https://api.quotable.io/quotes/random?tags=philosophy&limit=1"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                quote = data[0]
                return f'"{quote["content"]}" — {quote["author"]}'
    except Exception as e:
        print("Stoic quote API error:", e)
    
    # Fallback: hardcoded stoic quotes
    stoic_quotes = [
        '"You have power over your mind - not outside events. Realize this, and you will find strength." — Marcus Aurelius',
        '"Wealth consists not in having great possessions, but in having few wants." — Epictetus',
        '"We suffer more often in imagination than in reality." — Seneca',
        '"The happiness of your life depends upon the quality of your thoughts." — Marcus Aurelius',
        '"It\'s not what happens to you, but how you react to it that matters." — Epictetus',
        '"Luck is what happens when preparation meets opportunity." — Seneca',
        '"Waste no more time arguing about what a good man should be. Be one." — Marcus Aurelius',
        '"First say to yourself what you would be; and then do what you have to do." — Epictetus',
        '"True happiness is to enjoy the present, without anxious dependence upon the future." — Seneca',
        '"The best revenge is to be unlike him who performed the injury." — Marcus Aurelius',
    ]
    return random.choice(stoic_quotes)

# --- 7. Create digest message ---
def create_digest():
    now = datetime.now()
    raw_info = f"""📅 {now.strftime('%A, %d %B %Y, %H:%M')}
☀️ Weather in Kyiv: {get_weather()}
💵 {get_currency()}
💰 {get_crypto()}
📰 News:{get_news()}
🏛️ Daily Stoic: {get_stoic_quote()}""".strip()

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
