"""
fetch_ark_holdings.py — ARKWOOD FIU
Fetches current ARK ETF holdings to determine if tickers are held and at what conviction level.

Usage:
    python3 scripts/fetch_ark_holdings.py TSLA NVDA ROKU
    python3 scripts/fetch_ark_holdings.py TSLA --offline   # use cached snapshot

Output: JSON to stdout
Caches successful fetches to: data/snapshots/ark_holdings_YYYYMMDD.json
"""

import sys
import json
import csv
import io
import os
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print(json.dumps({"error": "requests not installed. Run: pip3 install requests"}))
    sys.exit(1)

ARK_ETFS = {
    "ARKK": "https://ark-funds.com/wp-content/uploads/funds-etf-csv/ARK_INNOVATION_ETF_ARKK_HOLDINGS.csv",
    "ARKW": "https://ark-funds.com/wp-content/uploads/funds-etf-csv/ARK_NEXT_GENERATION_INTERNET_ETF_ARKW_HOLDINGS.csv",
    "ARKG": "https://ark-funds.com/wp-content/uploads/funds-etf-csv/ARK_GENOMIC_REVOLUTION_ETF_ARKG_HOLDINGS.csv",
    "ARKF": "https://ark-funds.com/wp-content/uploads/funds-etf-csv/ARK_FINTECH_INNOVATION_ETF_ARKF_HOLDINGS.csv",
    "ARKQ": "https://ark-funds.com/wp-content/uploads/funds-etf-csv/ARK_AUTONOMOUS_TECH._&_ROBOTICS_ETF_ARKQ_HOLDINGS.csv",
    "ARKX": "https://ark-funds.com/wp-content/uploads/funds-etf-csv/ARK_SPACE_EXPLORATION_ETF_ARKX_HOLDINGS.csv",
}

SNAPSHOTS_DIR = Path(__file__).parent.parent / "data" / "snapshots"


def conviction_level(max_weight_pct: float) -> str:
    if max_weight_pct >= 5.0:
        return "HIGH"
    elif max_weight_pct >= 2.0:
        return "MEDIUM"
    elif max_weight_pct > 0:
        return "LOW"
    return "NONE"


def fetch_ark_universe() -> dict:
    """Fetch all ARK ETF holdings. Returns {ticker: [{etf, weight_pct, shares, market_value}]}"""
    universe = {}
    fetch_errors = []

    for etf_name, url in ARK_ETFS.items():
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "ARKWOOD-FIU/1.0"})
            if resp.status_code != 200:
                fetch_errors.append(f"{etf_name}: HTTP {resp.status_code}")
                continue

            # ARK CSVs sometimes have a header row before the actual CSV data
            text = resp.text
            lines = text.strip().splitlines()

            # Find the actual CSV header line (contains 'ticker' or 'symbol')
            header_idx = 0
            for i, line in enumerate(lines):
                if any(kw in line.lower() for kw in ["ticker", "symbol", "weight"]):
                    header_idx = i
                    break

            csv_text = "\n".join(lines[header_idx:])
            reader = csv.DictReader(io.StringIO(csv_text))

            for row in reader:
                # Normalize column names (ARK has changed them over time)
                ticker = (
                    row.get("ticker") or row.get("symbol") or row.get("Ticker") or row.get("Symbol") or ""
                ).strip().upper()

                if not ticker or ticker in ("", "-", "N/A"):
                    continue

                weight_str = row.get("weight (%)") or row.get("weight") or row.get("Weight (%)") or "0"
                shares_str = row.get("shares") or row.get("Shares") or "0"
                mv_str = row.get("market value ($)") or row.get("market value") or row.get("Market Value ($)") or "0"

                try:
                    weight_pct = float(weight_str.replace("%", "").replace(",", "").strip() or 0)
                    shares = float(shares_str.replace(",", "").strip() or 0)
                    market_value = float(mv_str.replace("$", "").replace(",", "").strip() or 0)
                except ValueError:
                    weight_pct, shares, market_value = 0.0, 0.0, 0.0

                if ticker not in universe:
                    universe[ticker] = []
                universe[ticker].append({
                    "etf": etf_name,
                    "weight_pct": round(weight_pct, 4),
                    "shares": int(shares),
                    "market_value_usd": int(market_value),
                })

            time.sleep(0.3)  # be polite to ARK servers

        except Exception as e:
            fetch_errors.append(f"{etf_name}: {str(e)}")

    return universe, fetch_errors


def load_cached_universe() -> dict:
    """Load the most recent ark_holdings snapshot from disk."""
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    snapshots = sorted(SNAPSHOTS_DIR.glob("ark_holdings_*.json"), reverse=True)
    if not snapshots:
        return None, "No cached ARK holdings found."
    with open(snapshots[0]) as f:
        data = json.load(f)
    return data.get("universe", {}), f"Loaded from cache: {snapshots[0].name}"


def save_universe_cache(universe: dict):
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    path = SNAPSHOTS_DIR / f"ark_holdings_{date_str}.json"
    # Also save as 'latest'
    latest_path = SNAPSHOTS_DIR / "ark_holdings_latest.json"
    payload = {"fetched_at": datetime.now(timezone.utc).isoformat(), "universe": universe}
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    with open(latest_path, "w") as f:
        json.dump(payload, f, indent=2)


def build_result(symbol: str, universe: dict) -> dict:
    holdings = universe.get(symbol, [])
    if not holdings:
        return {
            "ark_held": False,
            "total_etfs_held_in": 0,
            "holdings": [],
            "max_weight_pct": 0.0,
            "conviction_level": "NONE",
        }
    max_weight = max(h["weight_pct"] for h in holdings)
    return {
        "ark_held": True,
        "total_etfs_held_in": len(holdings),
        "holdings": sorted(holdings, key=lambda h: h["weight_pct"], reverse=True),
        "max_weight_pct": max_weight,
        "conviction_level": conviction_level(max_weight),
    }


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    offline = "--offline" in sys.argv
    tickers = [t.upper() for t in args]

    if not tickers:
        print(json.dumps({"error": "No tickers provided. Usage: fetch_ark_holdings.py TSLA NVDA"}))
        sys.exit(1)

    fetch_errors = []
    source = "live"

    if offline:
        universe, msg = load_cached_universe()
        if universe is None:
            print(json.dumps({"error": msg}))
            sys.exit(1)
        source = "cache"
        fetch_errors.append(msg)
    else:
        universe, fetch_errors = fetch_ark_universe()
        if universe:
            save_universe_cache(universe)
        else:
            # Fallback to cache
            cached, msg = load_cached_universe()
            if cached:
                universe = cached
                source = "cache_fallback"
                fetch_errors.append(f"Live fetch failed, falling back to cache: {msg}")
            else:
                universe = {}

    results = {symbol: build_result(symbol, universe) for symbol in tickers}

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "as_of": "daily",
        "data_quality": "PARTIAL" if fetch_errors else "FULL",
        "missing_fields": fetch_errors if fetch_errors else [],
        "source": source,
        "tickers": results,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
