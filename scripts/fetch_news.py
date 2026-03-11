"""
fetch_news.py — ARKWOOD FIU
Fetches recent news headlines for tickers via yfinance. Derives sentiment and catalyst scores.

Usage:
    python3 scripts/fetch_news.py TSLA NVDA

Output: JSON to stdout

Notes:
- Uses yfinance .news (sourced from Yahoo Finance/Google Finance).
- Sentiment is keyword-based — treat as a signal, not ground truth.
- recent_catalyst_score feeds into TVS Section C (Momentum & ARK Conviction).
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

POSITIVE_KEYWORDS = {
    "record", "breakthrough", "approval", "approved", "beat", "beats", "launch", "launched",
    "partnership", "wins", "win", "award", "upgrade", "outperform", "surge", "rally",
    "profit", "revenue growth", "record revenue", "new contract", "expansion", "acquisition",
    "milestone", "raises", "bullish", "strong", "exceeds", "ahead of",
}

NEGATIVE_KEYWORDS = {
    "miss", "misses", "investigation", "recall", "fine", "fined", "lawsuit", "sued",
    "downgrade", "dilution", "dilutive", "offering", "layoffs", "layoff", "cuts", "cut",
    "warning", "decline", "drops", "falls", "loss", "losses", "disappoints", "below",
    "disappointing", "probe", "breach", "hack", "regulatory", "ban", "blocked", "rejected",
    "bankruptcy", "debt", "subpoena",
}

LOOKBACK_DAYS = 30
MAX_ARTICLES = 10


def classify_sentiment(title: str) -> str:
    title_lower = title.lower()
    pos = any(kw in title_lower for kw in POSITIVE_KEYWORDS)
    neg = any(kw in title_lower for kw in NEGATIVE_KEYWORDS)
    if pos and not neg:
        return "POSITIVE"
    elif neg and not pos:
        return "NEGATIVE"
    elif pos and neg:
        return "MIXED"
    return "NEUTRAL"


def compute_catalyst_score(articles: list) -> int:
    """
    10 = 3+ positive in last 14 days, 0 negative
     5 = 1-2 positive or mixed signals
     0 = no positive, predominantly negative, or insufficient data
    """
    if not articles:
        return 0

    now_ts = datetime.now(timezone.utc).timestamp()
    recent_14d = [a for a in articles if (now_ts - a.get("published_ts", 0)) < 14 * 86400]

    positive_recent = sum(1 for a in recent_14d if a["sentiment_hint"] == "POSITIVE")
    negative_recent = sum(1 for a in recent_14d if a["sentiment_hint"] == "NEGATIVE")

    if positive_recent >= 3 and negative_recent == 0:
        return 10
    elif positive_recent >= 1 or any(a["sentiment_hint"] == "MIXED" for a in recent_14d):
        return 5
    return 0


def fetch_ticker(symbol: str) -> dict:
    missing = []
    try:
        tk = yf.Ticker(symbol)
        raw_news = tk.news

        if not raw_news:
            missing.append("news_feed")
            return {
                "data_quality": "EMPTY",
                "missing_fields": missing,
                "recent_catalyst_score": None,
                "article_count": 0,
                "articles": [],
                "_note": "No news returned — recent_catalyst_score set to null (Claude will note insufficient data)",
            }

        now_ts = datetime.now(timezone.utc).timestamp()
        cutoff_ts = now_ts - LOOKBACK_DAYS * 86400

        filtered = []
        for item in raw_news:
            # yfinance ≥0.2.x nests article data under item['content']
            content = item.get("content") or item
            title = content.get("title") or item.get("title", "")

            # pubDate is ISO string in new schema; providerPublishTime is unix int in old schema
            pub_date_str = content.get("pubDate") or content.get("displayTime", "")
            if pub_date_str:
                try:
                    from datetime import datetime as _dt
                    pub_ts = int(_dt.fromisoformat(pub_date_str.replace("Z", "+00:00")).timestamp())
                except Exception:
                    pub_ts = 0
            else:
                pub_ts = item.get("providerPublishTime", 0)

            if pub_ts < cutoff_ts:
                continue

            publisher = (
                content.get("provider", {}).get("displayName")
                or item.get("publisher", "")
            )
            link = (
                content.get("canonicalUrl", {}).get("url")
                or item.get("link", "")
            )

            sentiment = classify_sentiment(title)
            pub_dt = datetime.fromtimestamp(pub_ts, tz=timezone.utc).isoformat() if pub_ts else None
            filtered.append({
                "title": title,
                "publisher": publisher,
                "published_at": pub_dt,
                "published_ts": pub_ts,
                "link": link,
                "sentiment_hint": sentiment,
            })

        # Sort by recency, cap at MAX_ARTICLES
        filtered.sort(key=lambda x: x.get("published_ts", 0), reverse=True)
        articles = filtered[:MAX_ARTICLES]

        catalyst_score = compute_catalyst_score(articles)

        # Remove internal ts field from output
        output_articles = [{k: v for k, v in a.items() if k != "published_ts"} for a in articles]

        quality = "FULL" if articles else "EMPTY"
        return {
            "data_quality": quality,
            "missing_fields": missing,
            "recent_catalyst_score": catalyst_score,
            "article_count": len(articles),
            "articles": output_articles,
        }

    except Exception as e:
        return {
            "data_quality": "EMPTY",
            "missing_fields": ["all"],
            "recent_catalyst_score": None,
            "article_count": 0,
            "articles": [],
            "error": str(e),
        }


def main():
    tickers = [t.upper() for t in sys.argv[1:]]
    if not tickers:
        print(json.dumps({"error": "No tickers provided. Usage: fetch_news.py TSLA NVDA"}))
        sys.exit(1)

    results = {}
    for i, symbol in enumerate(tickers):
        results[symbol] = fetch_ticker(symbol)
        if i < len(tickers) - 1:
            time.sleep(0.5)

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "as_of": "last-30-days",
        "tickers": results,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
