"""
merge_data.py — ARKWOOD FIU
Merges JSON outputs from fetch scripts into a unified per-ticker structure.

Usage:
    python3 scripts/merge_data.py market.json fundamentals.json ark.json [news.json] > merged.json

Output: JSON to stdout
"""

import sys
import json
from datetime import datetime, timezone


def load_json(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {"_missing": True, "error": f"File not found: {path}"}
    except json.JSONDecodeError as e:
        return {"_missing": True, "error": f"JSON parse error in {path}: {e}"}


def main():
    paths = sys.argv[1:]
    if len(paths) < 3:
        print(json.dumps({"error": "Usage: merge_data.py market.json fundamentals.json ark.json [news.json] [technicals.json]"}))
        sys.exit(1)

    AS_OF_TO_KEY = {
        "realtime": "market",
        "trailing-12m": "fundamentals",
        "daily": "ark",
        "last-30-days": "news",
        "technicals": "technicals",
    }
    positional_keys = ["market", "fundamentals", "ark", "news", "technicals"]
    files = {}
    for i, path in enumerate(paths):
        data = load_json(path)
        as_of = data.get("as_of")
        key = AS_OF_TO_KEY.get(as_of) or (positional_keys[i] if i < len(positional_keys) else f"source_{i}")
        files[key] = data

    # Collect all ticker symbols across all files
    all_tickers = set()
    for key, data in files.items():
        if not data.get("_missing") and "tickers" in data:
            all_tickers.update(data["tickers"].keys())

    merged = {}
    for ticker in sorted(all_tickers):
        merged[ticker] = {}
        for key, data in files.items():
            if data.get("_missing"):
                merged[ticker][key] = {"_missing": True}
            else:
                merged[ticker][key] = data.get("tickers", {}).get(ticker, {"_missing": True})

    def source_meta(key: str, data: dict) -> dict:
        meta = {
            "fetched_at": data.get("fetched_at"),
            "as_of": data.get("as_of"),
            "data_quality": data.get("data_quality", "UNKNOWN"),
        }
        # Preserve macro gate fields from technicals source
        if key == "technicals":
            meta["macro_state"] = data.get("macro_state", "UNKNOWN")
            meta["spy_current_price"] = data.get("spy_current_price")
            meta["spy_sma_200"] = data.get("spy_sma_200")
        return meta

    output = {
        "merged_at": datetime.now(timezone.utc).isoformat(),
        "sources": {key: source_meta(key, data) for key, data in files.items()},
        "tickers": merged,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
