import requests
import time
import json
import csv
import os
from datetime import datetime, timedelta
import pytz
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# Download VADER lexicon (run once)
nltk.download('vader_lexicon')

# Initialize VADER sentiment analyzer
sid = SentimentIntensityAnalyzer()

# TradingView API endpoint
TV_URL = "https://news-mediator.tradingview.com/public/view/v1/symbol"

# List of symbols to fetch news for
SYMBOLS = [
    "BINANCE:BTCUSDT",
    "NASDAQ:AAPL",
    "FX:AUDUSD",
    "FX:EURAUD",
    "FX:EURGBP",
    "FX:EURJPY",
    "FX:EURUSD",
    "FX:GBPJPY",
    "FX:GBPUSD",
    "FX:NZDUSD",
    "FX:USDCAD",
    "FX:USDCHF",
    "FX:USDJPY"
]

# TradingView headers to mimic browser request
TV_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://in.tradingview.com",
    "Referer": "https://in.tradingview.com/",
    "Sec-Ch-Ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site"
}

# Function to categorize the news title
def categorize_title(title):
    title_lower = title.lower()
    if any(word in title_lower for word in ["earnings", "profit", "revenue", "quarterly results"]):
        return "Earnings"
    elif any(word in title_lower for word in ["dividend", "payout", "distribution"]):
        return "Dividends"
    elif any(word in title_lower for word in ["buyback", "repurchase", "share repurchase"]):
        return "Share buyback"
    elif any(word in title_lower for word in ["merger", "acquisition", "takeover", "m&a"]):
        return "Mergers and acquisition"
    elif any(word in title_lower for word in ["insider", "executive trading", "insider buying", "insider selling"]):
        return "Insider trading"
    elif any(word in title_lower for word in ["esg", "environmental", "sustainability", "regulation", "compliance"]):
        return "ESG and regulation"
    elif any(word in title_lower for word in ["analyst", "rating", "forecast", "outlook", "downgrade", "upgrade"]):
        return "Analysts"
    elif any(word in title_lower for word in ["credit rating", "bond rating", "debt rating"]):
        return "Credit ratings"
    else:
        return "News"

# Function to convert UTC timestamp to IST and extract date
def get_date_in_ist(published_at, current_time_ist):
    try:
        utc_time = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
        utc_time = pytz.utc.localize(utc_time)
        ist_tz = pytz.timezone("Asia/Kolkata")
        ist_time = utc_time.astimezone(ist_tz)
        date_str = ist_time.strftime("%Y-%m-%d")
        timestamp_str = ist_time.strftime("%Y-%m-%d %H:%M:%S")
        return date_str, timestamp_str, ist_time
    except (ValueError, TypeError):
        date_str = current_time_ist.strftime("%Y-%m-%d")
        timestamp_str = current_time_ist.strftime("%Y-%m-%d %H:%M:%S")
        return date_str, timestamp_str, current_time_ist

# Function to analyze sentiment of a news title
def analyze_sentiment(title):
    if not title or title == "No title":
        return "Neutral"
    scores = sid.polarity_scores(title)
    compound = scores['compound']
    if compound >= 0.05:
        return "Positive"
    elif compound <= -0.05:
        return "Negative"
    else:
        return "Neutral"

# Function to calculate net sentiment from news buffer
def calculate_net_sentiment(news_buffer, cutoff_time):
    positive = sum(1 for item in news_buffer if item['sentiment'] == "Positive" and item['timestamp'] >= cutoff_time)
    negative = sum(1 for item in news_buffer if item['sentiment'] == "Negative" and item['timestamp'] >= cutoff_time)
    neutral = sum(1 for item in news_buffer if item['sentiment'] == "Neutral" and item['timestamp'] >= cutoff_time)
    total_items = positive + negative + neutral
    score = positive - negative
    if neutral > positive and neutral > negative:
        return "Neutral", score, positive, negative, neutral, total_items
    elif score > 0:
        return "Positive", score, positive, negative, neutral, total_items
    elif score < 0:
        return "Negative", score, positive, negative, neutral, total_items
    else:
        return "Neutral", score, positive, negative, neutral, total_items

# Function to prune old news
def prune_old_news(symbol, news_buffer, last_titles, cutoff_time):
    news_buffer[symbol] = [item for item in news_buffer[symbol] if item['timestamp'] >= cutoff_time]
    last_titles[symbol] = {f"{item['title']}:{item['published_at']}" for item in news_buffer[symbol]}

# Initialize tracking structures
last_titles = {symbol: set() for symbol in SYMBOLS}
initial_fetch_done = {symbol: False for symbol in SYMBOLS}
news_buffer = {symbol: [] for symbol in SYMBOLS}

# Load existing news buffer from summary file, if available
summary_file = "sentiment_summary.json"
if os.path.isfile(summary_file):
    try:
        with open(summary_file, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        ist_tz = pytz.timezone("Asia/Kolkata")
        cutoff_time = datetime.now(ist_tz) - timedelta(days=7)
        for symbol in SYMBOLS:
            if symbol in loaded_data:
                for item in loaded_data[symbol].get("news", []):
                    try:
                        timestamp = datetime.strptime(item['published_at'], "%Y-%m-%d %H:%M:%S")
                        timestamp = ist_tz.localize(timestamp)
                        if timestamp >= cutoff_time:
                            news_buffer[symbol].append({
                                "title": item['title'],
                                "sentiment": item['sentiment'],
                                "timestamp": timestamp,
                                "published_at": item['published_at']
                            })
                            last_titles[symbol].add(f"{item['title']}:{item['published_at']}")
                    except ValueError as e:
                        print(f"Error parsing timestamp in sentiment_summary.json for {symbol}: {e}")
    except Exception as e:
        print(f"Error loading sentiment_summary.json: {e}")

while True:
    ist_tz = pytz.timezone("Asia/Kolkata")
    current_time_ist = datetime.now(ist_tz)
    cutoff_time = current_time_ist - timedelta(days=7)
    date_str = current_time_ist.strftime("%Y-%m-%d")
    timestamp_str = current_time_ist.strftime("%Y-%m-%d %H:%M:%S")

    for symbol in SYMBOLS:
        try:
            # Prune old news
            prune_old_news(symbol, news_buffer, last_titles, cutoff_time)

            TV_PARAMS = {
                "filter": ["lang:en", f"symbol:{symbol}"],
                "client": "web"
            }

            response = requests.get(TV_URL, params=TV_PARAMS, headers=TV_HEADERS, timeout=10)
            response.raise_for_status()

            symbol_data = response.json()
            news_items = symbol_data.get("items", [])
            if news_items:
                # Sort news items by published_at (newest first)
                news_items.sort(key=lambda x: x.get("published_at", ""), reverse=True)
                items_to_process = news_items[:50] if not initial_fetch_done[symbol] else [news_items[0]]
                initial_fetch_done[symbol] = True
                if len(items_to_process) > 1 and initial_fetch_done[symbol]:
                    print(f"Warning: Multiple news items returned for {symbol}, processing only the newest.")

                for item in items_to_process:
                    title = item.get("title", "No title")
                    published_at = item.get("published_at", None)
                    title_key = f"{title}:{published_at}"

                    if title_key not in last_titles[symbol]:
                        category = categorize_title(title)
                        sentiment = analyze_sentiment(title)
                        date_str_news, published_at_ist, timestamp = get_date_in_ist(published_at, current_time_ist)
                        print(f"Symbol: {symbol} | Category: {category} | Sentiment: {sentiment} | Published: {published_at_ist} | Latest news: {title}")

                        # Add to news buffer
                        news_buffer[symbol].append({
                            "title": title,
                            "sentiment": sentiment,
                            "timestamp": timestamp,
                            "published_at": published_at_ist
                        })
                        # Cap buffer at 100 items
                        if len(news_buffer[symbol]) > 100:
                            news_buffer[symbol] = news_buffer[symbol][-100:]

                        news_entry = {
                            "symbol": symbol,
                            "category": category,
                            "sentiment": sentiment,
                            "published_at": published_at_ist,
                            "title": title
                        }

                        symbol_safe = symbol.replace(":", "_")
                        csv_filename = f"{symbol_safe}_{date_str_news}.csv"
                        json_filename = f"{symbol_safe}_{date_str_news}.json"

                        csv_headers = ["symbol", "category", "sentiment", "published_at", "title"]
                        file_exists = os.path.isfile(csv_filename)
                        with open(csv_filename, mode="a", newline="", encoding="utf-8") as csv_file:
                            writer = csv.DictWriter(csv_file, fieldnames=csv_headers)
                            if not file_exists:
                                writer.writeheader()
                            writer.writerow(news_entry)

                        json_data = []
                        if os.path.isfile(json_filename):
                            with open(json_filename, "r", encoding="utf-8") as json_file:
                                json_data = json.load(json_file)
                        json_data.append(news_entry)
                        with open(json_filename, "w", encoding="utf-8") as json_file:
                            json.dump(json_data, json_file, indent=2)

                        last_titles[symbol].add(title_key)
                    else:
                        print(f"Duplicate news skipped for {symbol}: {title}")
            else:
                print(f"No news items found for {symbol}.")

        except requests.exceptions.RequestException as e:
            print(f"An error occurred for {symbol}: {e}")

    # Calculate and display net sentiment for all symbols (7-day window)
    print("\n--- Net Sentiment Summary (Last 7 Days) ---")
    summary_data = {}
    summary_csv_data = []
    for symbol in SYMBOLS:
        net_sentiment, score, positive, negative, neutral, total_items = calculate_net_sentiment(news_buffer[symbol], cutoff_time)
        print(f"Net Sentiment: {symbol}: {net_sentiment} (Score: {score}, Positive: {positive}, Negative: {negative}, Neutral: {neutral}, TotalItems: {total_items})")
        
        # Prepare data for date-specific JSON and persistence
        summary_data[symbol] = {
            "news": [
                {
                    "title": item['title'],
                    "sentiment": item['sentiment'],
                    "published_at": item['published_at']
                } for item in news_buffer[symbol]
            ],
            "NetSentiment": net_sentiment,
            "Score": score,
            "Positive": positive,
            "Negative": negative,
            "Neutral": neutral,
            "TotalItems": total_items
        }

        # Prepare data for date-specific and historical CSV
        summary_csv_data.append({
            "symbol": symbol,
            "NetSentiment": net_sentiment,
            "Score": score,
            "Positive": positive,
            "Negative": negative,
            "Neutral": neutral,
            "TotalItems": total_items,
            "Timestamp": timestamp_str
        })

    # Save sentiment summary to single JSON file (for news_buffer persistence)
    try:
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2)
    except Exception as e:
        print(f"Error saving sentiment_summary.json: {e}")

    # Save Net Sentiment Summary to date-specific CSV
    summary_csv_filename = f"sentiment_summary_{date_str}.csv"
    summary_csv_headers = ["symbol", "NetSentiment", "Score", "Positive", "Negative", "Neutral", "TotalItems", "Timestamp"]
    try:
        with open(summary_csv_filename, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=summary_csv_headers)
            writer.writeheader()
            for entry in summary_csv_data:
                writer.writerow(entry)
    except Exception as e:
        print(f"Error saving {summary_csv_filename}: {e}")

    # Save Net Sentiment Summary to date-specific JSON
    summary_json_filename = f"sentiment_summary_{date_str}.json"
    summary_json_data = {
        symbol: {
            "NetSentiment": data["NetSentiment"],
            "Score": data["Score"],
            "Positive": data["Positive"],
            "Negative": data["Negative"],
            "Neutral": data["Neutral"],
            "TotalItems": data["TotalItems"],
            "Timestamp": timestamp_str
        } for symbol, data in summary_data.items()
    }
    try:
        with open(summary_json_filename, "w", encoding="utf-8") as json_file:
            json.dump(summary_json_data, json_file, indent=2)
    except Exception as e:
        print(f"Error saving {summary_json_filename}: {e}")

    # Save Net Sentiment Summary to historical CSV
    historical_csv_filename = "historical_net_sentiment_summary.csv"
    historical_csv_headers = ["symbol", "NetSentiment", "Score", "Positive", "Negative", "Neutral", "TotalItems", "Timestamp"]
    try:
        file_exists = os.path.isfile(historical_csv_filename)
        with open(historical_csv_filename, mode="a", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=historical_csv_headers)
            if not file_exists:
                writer.writeheader()
            for entry in summary_csv_data:
                writer.writerow(entry)
    except Exception as e:
        print(f"Error saving {historical_csv_filename}: {e}")

    # Save Net Sentiment Summary to historical JSON
    historical_json_filename = "historical_net_sentiment_summary.json"
    historical_json_data = []
    try:
        if os.path.isfile(historical_json_filename):
            with open(historical_json_filename, "r", encoding="utf-8") as json_file:
                historical_json_data = json.load(json_file)
    except Exception as e:
        print(f"Error loading {historical_json_filename}: {e}")
    historical_json_data.append({
        "Timestamp": timestamp_str,
        "symbols": summary_json_data
    })
    try:
        with open(historical_json_filename, "w", encoding="utf-8") as json_file:
            json.dump(historical_json_data, json_file, indent=2)
    except Exception as e:
        print(f"Error saving {historical_json_filename}: {e}")

    time.sleep(60)