"""
fetch_technicals.py — ARKWOOD FIU
Fetches technical indicators for one or more tickers via yfinance.

Usage:
    python3 scripts/fetch_technicals.py TSLA NVDA ROKU

Output: JSON to stdout

Signals computed:
    - Trend:            SMA50 vs SMA200 → UPTREND / DOWNTREND / FLAT
    - Momentum:         RSI-14          → BULLISH / NEUTRAL / OVERBOUGHT / OVERSOLD
    - Breakout:         vs 52w range    → BREAKING_OUT / RANGE / BREAKING_DOWN
    - Relative Strength: vs SPY         → LEADING / IN_LINE / LAGGING
"""

import sys
import json
import time
from datetime import datetime, timezone

try:
    import pandas as pd
    import yfinance as yf
except ImportError:
    print(json.dumps({"error": "yfinance/pandas not installed. Run: pip3 install yfinance pandas"}))
    sys.exit(1)

# --- Constants ---
RATE_LIMIT_SECS: float = 0.5
VOLUME_LOOKBACK_DAYS: int = 20
RSI_PERIOD: int = 14
SMA_SHORT: int = 50
SMA_LONG: int = 200
FLAT_THRESHOLD_PCT: float = 0.01          # ±1% band for FLAT trend
BREAKING_OUT_THRESHOLD_PCT: float = 0.03  # within 3% of 52w high
BREAKING_DOWN_52W_PCT: float = 0.10       # within 10% of 52w low
BREAKING_DOWN_SMA_PCT: float = 0.90       # price < sma50 * 0.90
EXTENDED_SMA50_THRESHOLD: float = 0.15    # >15% above SMA50 → EXTENDED


def compute_rsi(closes: "pd.Series", period: int = RSI_PERIOD) -> "float | None":
    """
    Wilder's smoothed RSI using EWM (alpha = 1/period).
    Returns 50.0 if all price changes are zero (edge case).
    Returns None if fewer than period+1 data points.
    """
    if len(closes) < period + 1:
        return None
    delta = closes.diff().dropna()
    gains = delta.clip(lower=0)
    losses = (-delta).clip(lower=0)
    avg_gain = gains.ewm(com=period - 1, min_periods=period).mean().iloc[-1]
    avg_loss = losses.ewm(com=period - 1, min_periods=period).mean().iloc[-1]
    if avg_loss == 0:
        return 50.0 if avg_gain == 0 else 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def compute_sma(closes: "pd.Series", window: int) -> "float | None":
    """Simple moving average of the last `window` closes. Returns None if insufficient data."""
    if len(closes) < window:
        return None
    return round(float(closes.iloc[-window:].mean()), 4)


def compute_return(closes: "pd.Series", lookback_days: int) -> "float | None":
    """
    Price return over approximately `lookback_days` trading days.
    lookback_days=21 ≈ 1 month; lookback_days=63 ≈ 3 months.
    """
    if len(closes) < lookback_days + 1:
        return None
    end = float(closes.iloc[-1])
    start = float(closes.iloc[-(lookback_days + 1)])
    if start == 0:
        return None
    return round((end - start) / start, 4)


def classify_trend(sma50: "float | None", sma200: "float | None") -> str:
    """UPTREND / DOWNTREND / FLAT based on SMA50 vs SMA200 with ±1% flat band."""
    if sma50 is None or sma200 is None:
        return "FLAT"
    ratio = sma50 / sma200
    if ratio > 1 + FLAT_THRESHOLD_PCT:
        return "UPTREND"
    elif ratio < 1 - FLAT_THRESHOLD_PCT:
        return "DOWNTREND"
    return "FLAT"


def classify_momentum(rsi: "float | None") -> str:
    """
    OVERSOLD   < 35
    NEUTRAL    35–45 or 65–70
    BULLISH    45–65
    OVERBOUGHT > 70
    """
    if rsi is None:
        return "NEUTRAL"
    if rsi > 70:
        return "OVERBOUGHT"
    if rsi < 35:
        return "OVERSOLD"
    if 45 <= rsi < 65:
        return "BULLISH"
    return "NEUTRAL"


def classify_breakout(
    current_price: "float | None",
    high_52w: "float | None",
    low_52w: "float | None",
    sma50: "float | None",
    current_volume: "float | None",
    avg_volume_20d: "float | None",
) -> str:
    """
    BREAKING_OUT  — within 3% of 52w high AND current volume above 20-day avg
    BREAKING_DOWN — within 10% of 52w low OR price < sma50 * 0.90
    RANGE         — all other cases
    BREAKING_OUT is checked first.
    """
    if current_price is None:
        return "RANGE"

    # BREAKING_OUT
    if high_52w and high_52w > 0:
        pct_from_high = (high_52w - current_price) / high_52w
        volume_ok = (
            current_volume is not None
            and avg_volume_20d is not None
            and avg_volume_20d > 0
            and current_volume > avg_volume_20d
        )
        if pct_from_high <= BREAKING_OUT_THRESHOLD_PCT and volume_ok:
            return "BREAKING_OUT"

    # BREAKING_DOWN
    if low_52w and low_52w > 0:
        pct_from_low = (current_price - low_52w) / low_52w
        if pct_from_low <= BREAKING_DOWN_52W_PCT:
            return "BREAKING_DOWN"
    if sma50 and sma50 > 0 and current_price < sma50 * BREAKING_DOWN_SMA_PCT:
        return "BREAKING_DOWN"

    return "RANGE"


def classify_rs(
    return_1m: "float | None",
    return_3m: "float | None",
    spy_return_1m: "float | None",
    spy_return_3m: "float | None",
) -> str:
    """
    LEADING  — outperforms SPY on both 1m and 3m
    LAGGING  — underperforms SPY on both 1m and 3m
    IN_LINE  — all other cases (mixed or any None)
    """
    if any(v is None for v in [return_1m, return_3m, spy_return_1m, spy_return_3m]):
        return "IN_LINE"
    if return_1m > spy_return_1m and return_3m > spy_return_3m:
        return "LEADING"
    if return_1m < spy_return_1m and return_3m < spy_return_3m:
        return "LAGGING"
    return "IN_LINE"


def fetch_spy_returns() -> dict:
    """
    Fetches SPY 1y history once. Returns spy_return_1m and spy_return_3m.
    Returns None values if fetch fails — non-fatal.
    """
    try:
        hist = yf.Ticker("SPY").history(period="1y")
        if hist.empty:
            return {"spy_return_1m": None, "spy_return_3m": None}
        closes = hist["Close"]
        return {
            "spy_return_1m": compute_return(closes, 21),
            "spy_return_3m": compute_return(closes, 63),
        }
    except Exception:
        return {"spy_return_1m": None, "spy_return_3m": None}


def fetch_ticker(symbol: str, spy_returns: dict) -> dict:
    """
    Fetches 1y daily history for `symbol` and computes all technical signals.
    Returns a dict conforming to the technicals output schema.
    """
    missing = []

    try:
        hist = yf.Ticker(symbol).history(period="1y")
        if hist is None or hist.empty:
            return {
                "data_quality": "EMPTY",
                "missing_fields": ["all"],
                "error": f"No price history returned for {symbol}",
            }

        closes = hist["Close"]
        current_price = float(closes.iloc[-1]) if len(closes) > 0 else None

        # SMAs
        sma_50 = compute_sma(closes, SMA_SHORT)
        sma_200 = compute_sma(closes, SMA_LONG)
        if sma_50 is None:
            missing.append("sma_50")
        if sma_200 is None:
            missing.append("sma_200")

        price_vs_sma50_pct = None
        if current_price and sma_50 and sma_50 > 0:
            price_vs_sma50_pct = round((current_price - sma_50) / sma_50, 4)
        else:
            missing.append("price_vs_sma50_pct")

        # RSI
        rsi_14 = compute_rsi(closes, RSI_PERIOD)
        if rsi_14 is None:
            missing.append("rsi_14")

        # 52-week high/low from full 1y history
        high_52w = round(float(hist["High"].max()), 4) if not hist.empty else None
        low_52w = round(float(hist["Low"].min()), 4) if not hist.empty else None

        price_vs_52w_high_pct = None
        price_vs_52w_low_pct = None
        if current_price and high_52w and high_52w > 0:
            price_vs_52w_high_pct = round((current_price - high_52w) / high_52w, 4)
        else:
            missing.append("price_vs_52w_high_pct")
        if current_price and low_52w and low_52w > 0:
            price_vs_52w_low_pct = round((current_price - low_52w) / low_52w, 4)
        else:
            missing.append("price_vs_52w_low_pct")

        # Volume
        current_volume = float(hist["Volume"].iloc[-1]) if len(hist) > 0 else None
        avg_volume_20d = (
            round(float(hist["Volume"].iloc[-VOLUME_LOOKBACK_DAYS:].mean()), 0)
            if len(hist) >= VOLUME_LOOKBACK_DAYS
            else None
        )
        if current_volume is None:
            missing.append("current_volume")
        if avg_volume_20d is None:
            missing.append("avg_volume_20d")

        # Returns
        return_1m = compute_return(closes, 21)
        return_3m = compute_return(closes, 63)
        if return_1m is None:
            missing.append("return_1m")
        if return_3m is None:
            missing.append("return_3m")

        spy_return_1m = spy_returns.get("spy_return_1m")
        spy_return_3m = spy_returns.get("spy_return_3m")

        # Classify signals
        trend_signal = classify_trend(sma_50, sma_200)
        momentum_signal = classify_momentum(rsi_14)
        breakout_signal = classify_breakout(
            current_price, high_52w, low_52w, sma_50, current_volume, avg_volume_20d
        )
        rs_signal = classify_rs(return_1m, return_3m, spy_return_1m, spy_return_3m)

        data_quality = "FULL" if len(missing) == 0 else ("PARTIAL" if len(missing) < 5 else "EMPTY")

        return {
            "data_quality": data_quality,
            "missing_fields": missing,
            "sma_50": sma_50,
            "sma_200": sma_200,
            "price_vs_sma50_pct": price_vs_sma50_pct,
            "trend_signal": trend_signal,
            "rsi_14": rsi_14,
            "momentum_signal": momentum_signal,
            "price_vs_52w_high_pct": price_vs_52w_high_pct,
            "price_vs_52w_low_pct": price_vs_52w_low_pct,
            "breakout_signal": breakout_signal,
            "return_1m": return_1m,
            "return_3m": return_3m,
            "spy_return_1m": spy_return_1m,
            "spy_return_3m": spy_return_3m,
            "rs_signal": rs_signal,
        }

    except Exception as e:
        return {
            "data_quality": "EMPTY",
            "missing_fields": ["all"],
            "error": str(e),
        }


def main():
    tickers = [t.upper() for t in sys.argv[1:]]
    if not tickers:
        print(json.dumps({"error": "No tickers provided. Usage: fetch_technicals.py TSLA NVDA"}))
        sys.exit(1)

    spy_returns = fetch_spy_returns()

    results = {}
    for i, symbol in enumerate(tickers):
        results[symbol] = fetch_ticker(symbol, spy_returns)
        if i < len(tickers) - 1:
            time.sleep(RATE_LIMIT_SECS)

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "as_of": "technicals",
        "tickers": results,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
