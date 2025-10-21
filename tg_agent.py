import os
import requests
from datetime import datetime
from openai import OpenAI

# Ініціалізуємо клієнт OpenAI
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Telegram
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# --- 1. Отримуємо погоду ---
def get_weather():
    try:
        url = "https://wttr.in/Kyiv?format=%C+%t"
        return requests.get(url).text.strip()
    except:
        return "Не вдалося отримати погоду."

# --- 2. Курси криптовалют ---
def get_crypto():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
        data = requests.get(url).json()
        btc = data["bitcoin"]["usd"]
        eth = data["ethereum"]["usd"]
        return f"BTC: ${btc} | ETH: ${eth}"
    except:
        return "Не вдалося отримати курси криптовалют."

# --- 3. Курси валют до гривні ---
def get_currency():
    try:
        url = "https://api.minfin.com.ua/mb/2d7f0dc6f4e8843e93f8a7e5b123456789/"  # Псевдо-ключ, пояснення нижче
        # якщо API недоступне, беремо з monobank
        mono = requests.get("https://api.monobank.ua/bank/currency").json()
        usd = next((x for x in mono if x["currencyCodeA"] == 840 and x["currencyCodeB"] == 980), None)
        eur = next((x for x in mono if x["currencyCodeA"] == 978 and x["currencyCodeB"] == 980), None)
        usd_rate = f"USD: {usd['rateBuy']:.2f}/{usd['rateSell']:.2f}"
        eur_rate = f"EUR: {eur['rateBuy']:.2f}/{eur['rateSell']:.2f}"
        return f"{usd_rate} | {eur_rate}"
    except:
        return "Не вдалося отримати курси валют."

# --- 4. Новини ---
def get_news():
    try:
        url = "https://newsapi.org/v2/top-headlines?category=technology&language=en&apiKey=1f3f2d5e123d4567890fake"
        data = requests.get(url).json()
        articles = [a["title"] for a in data["articles"][:3]]
        return "\n• ".join(articles)
    except:
        return "Не вдалося отримати новини."

# --- 5. Цікавий факт ---
def get_fact():
    try:
        return requests.get("http://numbersapi.com/today/date").text
    except:
        return "Не вдалося отримати факт."

# --- 6. Формуємо текст дайджесту ---
def create_digest():
    now = datetime.now()
    info = f"""
📅 {now.strftime('%A, %d %B %Y, %H:%M')}
☀️ Погода в Києві: {get_weather()}
💵 Валюта: {get_currency()}
💰 Крипта: {get_crypto()}
📰 Новини:
• {get_news()}
💡 Цікавий факт: {get_fact()}
"""

    prompt = f"Склади короткий,
