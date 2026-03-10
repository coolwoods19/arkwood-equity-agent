"""
fetch_market_data.py — ARKWOOD FIU
Fetches current market data for one or more tickers via yfinance.

Usage:
    python3 scripts/fetch_market_data.py TSLA NVDA ROKU

Output: JSON to stdout
"""

import sys
import json
import time
from datetime import datetime, timezone

try:
    import yfinance as yf
except ImportError:
    print(json.dumps({"error": "yfinance not installed. Run: pip3 install yfinance"}))
    sys.exit(1)


def fetch_ticker(symbol: str) -> dict:
    missing = []
    data = {}

    try:
        tk = yf.Ticker(symbol)
        info = tk.info or {}

        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
            return {
                "data_quality": "EMPTY",
                "missing_fields": ["all"],
                "error": f"No data returned for {symbol}",
            }

        def get(key, fallback=None):
            val = info.get(key, fallback)
            if val is None:
                missing.append(key)
            return val

        current_price = get("currentPrice") or get("regularMarketPrice")
        fifty_two_high = get("fiftyTwoWeekHigh")
        fifty_two_low = get("fiftyTwoWeekLow")

        price_vs_52w_high = None
        if current_price and fifty_two_high:
            price_vs_52w_high = round(current_price / fifty_two_high, 4)

        # 1-year price history for YTD return
        ytd_return = None
        price_history = []
        try:
            hist = tk.history(period="1y")
            if not hist.empty:
                first_close = float(hist["Close"].iloc[0])
                last_close = float(hist["Close"].iloc[-1])
                if first_close:
                    ytd_return = round((last_close - first_close) / first_close, 4)
                price_history = [
                    {"date": str(d.date()), "close": round(float(c), 4)}
                    for d, c in zip(hist.index[-30:], hist["Close"].iloc[-30:])
                ]
        except Exception:
            missing.append("price_history_1y")
            missing.append("ytd_return")

        data = {
            "short_name": get("shortName"),
            "long_name": get("longName"),
            "current_price": current_price,
            "market_cap": get("marketCap"),
            "beta": get("beta"),
            "fifty_two_week_high": fifty_two_high,
            "fifty_two_week_low": fifty_two_low,
            "price_vs_52w_high": price_vs_52w_high,
            "average_volume": get("averageVolume"),
            "regular_market_volume": get("regularMarketVolume"),
            "ytd_return": ytd_return,
            "sector": get("sector"),
            "industry": get("industry"),
            "price_history_30d": price_history,
        }

        quality = "FULL" if len(missing) == 0 else ("PARTIAL" if len(missing) < 5 else "EMPTY")
        return {"data_quality": quality, "missing_fields": missing, **data}

    except Exception as e:
        return {
            "data_quality": "EMPTY",
            "missing_fields": ["all"],
            "error": str(e),
        }


def main():
    tickers = [t.upper() for t in sys.argv[1:]]
    if not tickers:
        print(json.dumps({"error": "No tickers provided. Usage: fetch_market_data.py TSLA NVDA"}))
        sys.exit(1)

    results = {}
    for i, symbol in enumerate(tickers):
        results[symbol] = fetch_ticker(symbol)
        if i < len(tickers) - 1:
            time.sleep(0.5)  # avoid 429s

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "as_of": "realtime",
        "tickers": results,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
