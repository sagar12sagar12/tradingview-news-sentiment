# TradingView News Sentiment Analysis

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

This project fetches financial news from the TradingView API, performs sentiment analysis using NLTK's VADER, and generates real-time sentiment summaries for trading symbols. It tracks news for a 7-day window, categorizes news (e.g., Earnings, Dividends), and outputs detailed CSV and JSON files for analysis. The script is designed for traders to monitor market sentiment and inform trading decisions.

## Features
- **Real-Time News Fetching**: Pulls news every 60 seconds for symbols like `BINANCE:BTCUSDT`, `FX:GBPUSD`, and more.
- **Sentiment Analysis**: Uses VADER to classify news as Positive, Negative, or Neutral.
- **Net Sentiment Scoring**: Calculates `Score = Positive - Negative`, with Neutral sentiment prioritized when Neutral counts dominate.
- **Historical Tracking**: Maintains a historical record of Net Sentiment Summaries.
- **Output Files**:
  - Per-symbol news: `SYMBOL_YYYY-MM-DD.csv/json` (appended).
  - Daily Net Sentiment Summary: `sentiment_summary_YYYY-MM-DD.csv/json` (overwritten).
  - Historical Net Sentiment Summary: `historical_net_sentiment_summary.csv/json` (appended).
  - Persistent news buffer: `sentiment_summary.json` (overwritten).

## Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Internet connection (for TradingView API and NLTK data download)

## Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/tradingview-news-sentiment.git
   cd tradingview-news-sentiment
   ```

2. **Create a Virtual Environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Script**:
   ```bash
   python tradingview_news_sentiment.py
   ```

   Note: The script downloads the NLTK VADER lexicon on first run, requiring an internet connection.

## Usage
- Run `tradingview_news_sentiment.py` to start fetching news and generating outputs.
- The script runs indefinitely, updating every 60 seconds.
- Press `Ctrl+C` to stop.
- Check the console for real-time sentiment updates and output files in the project directory.

### Output Files
- **Per-Symbol News** (`SYMBOL_YYYY-MM-DD.csv/json`):
  - Appends individual news items.
  - Fields: `symbol`, `category`, `sentiment`, `published_at`, `title`.
- **Daily Net Sentiment Summary** (`sentiment_summary_YYYY-MM-DD.csv/json`):
  - Overwrites each minute with the latest summary.
  - Fields: `symbol`, `NetSentiment`, `Score`, `Positive`, `Negative`, `Neutral`, `TotalItems`, `Timestamp`.
- **Historical Net Sentiment Summary** (`historical_net_sentiment_summary.csv/json`):
  - Appends each minute’s summary for historical analysis.
  - CSV: Same fields as daily summary.
  - JSON: List of timestamped entries, each containing a `symbols` dictionary.
- **Persistent News Buffer** (`sentiment_summary.json`):
  - Stores the news buffer for persistence across runs.
  - Includes news items and summary data per symbol.

### Example Output
**Console** (at 16:08 IST, May 16, 2025):
```
Symbol: FX:GBPUSD | Category: News | Sentiment: Positive | Published: 2025-05-16 16:07:30 | Latest news: GBPUSD rises on UK data
No news items found for BINANCE:BTCUSDT.

--- Net Sentiment Summary (Last 7 Days) ---
Net Sentiment: BINANCE:BTCUSDT: Neutral (Score: 0, Positive: 0, Negative: 0, Neutral: 100, TotalItems: 100)
Net Sentiment: FX:GBPUSD: Neutral (Score: 41, Positive: 41, Negative: 0, Neutral: 59, TotalItems: 100)
...
```

**Sample CSV** (`sentiment_summary_2025-05-16.csv`):
```
symbol,NetSentiment,Score,Positive,Negative,Neutral,TotalItems,Timestamp
BINANCE:BTCUSDT,Neutral,0,0,0,100,100,2025-05-16 16:08:00
FX:GBPUSD,Neutral,41,41,0,59,100,2025-05-16 16:08:00
...
```

**Sample JSON** (`historical_net_sentiment_summary.json`):
```json
[
  {
    "Timestamp": "2025-05-16 16:08:00",
    "symbols": {
      "FX:GBPUSD": {
        "NetSentiment": "Neutral",
        "Score": 41,
        "Positive": 41,
        "Negative": 0,
        "Neutral": 59,
        "TotalItems": 100,
        "Timestamp": "2025-05-16 16:08:00"
      },
      ...
    }
  }
]
```

See the `example_output/` directory for more samples.

## Troubleshooting
- **NLTK Download Error**: Ensure internet access and re-run the script to download `vader_lexicon`.
- **API Errors**: Check TradingView API status or rate limits. Errors are logged to the console.
- **Large Historical Files**: Monitor `historical_net_sentiment_summary.csv/json` size and prune manually if needed.
- **Timestamp Issues**: Ensure system time is correct, as timestamps are in IST.

## Contributing
Contributions are welcome! Please:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit changes (`git commit -m 'Add your feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a Pull Request.

Report issues or suggest features via [GitHub Issues](https://github.com/your-username/tradingview-news-sentiment/issues).

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact
For questions or support, open an issue on [GitHub](https://github.com/your-username/tradingview-news-sentiment/issues).

## Future Enhancements
- Add database storage for historical data.
- Implement sentiment trend visualization.
- Support weighted sentiment (e.g., recent news weighted higher).
- Add configurable symbols and intervals.