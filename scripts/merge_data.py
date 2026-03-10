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
        print(json.dumps({"error": "Usage: merge_data.py market.json fundamentals.json ark.json [news.json]"}))
        sys.exit(1)

    key_names = ["market", "fundamentals", "ark", "news"]
    files = {}
    for i, path in enumerate(paths):
        key = key_names[i] if i < len(key_names) else f"source_{i}"
        files[key] = load_json(path)

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

    output = {
        "merged_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            key: {
                "fetched_at": data.get("fetched_at"),
                "as_of": data.get("as_of"),
                "data_quality": data.get("data_quality", "UNKNOWN"),
            }
            for key, data in files.items()
        },
        "tickers": merged,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
