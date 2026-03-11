"""
csv_reader.py — ARKWOOD FIU
Reads portfolio.csv and watchlist.csv into typed dicts.
All files are opened read-only. portfolio.csv is never written.
"""

import csv
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _float_or_none(val: str) -> Optional[float]:
    val = val.strip()
    if not val:
        return None
    try:
        return float(val)
    except ValueError:
        return None


def _int_or_none(val: str) -> Optional[int]:
    val = val.strip()
    if not val:
        return None
    try:
        return int(val)
    except ValueError:
        return None


def read_portfolio() -> list[dict]:
    path = DATA_DIR / "portfolio.csv"
    holdings = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row["ticker"].strip().upper()
            if not ticker:
                continue
            holdings.append({
                "ticker": ticker,
                "shares": _float_or_none(row.get("shares", "")),
                "avg_cost": _float_or_none(row.get("avg_cost", "")),
                "purchase_value": _float_or_none(row.get("purchase_value", "")),
                "target_weight": _float_or_none(row.get("target_weight", "")),
                "max_weight": _float_or_none(row.get("max_weight", "")),
                "alert_below": _float_or_none(row.get("alert_below", "")),
                "alert_above": _float_or_none(row.get("alert_above", "")),
                "sector": row.get("sector", "").strip(),
                "thesis_confidence": row.get("thesis_confidence", "").strip().upper() or None,
                "last_reviewed": row.get("last_reviewed", "").strip() or None,
                "notes": row.get("notes", "").strip() or None,
            })
    return holdings


def read_watchlist() -> list[dict]:
    path = DATA_DIR / "watchlist.csv"
    items = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row["ticker"].strip().upper()
            if not ticker:
                continue
            items.append({
                "ticker": ticker,
                "sector": row.get("sector", "").strip(),
                "why_watching": row.get("why_watching", "").strip(),
                "target_entry": _float_or_none(row.get("target_entry", "")),
                "priority": row.get("priority", "").strip().upper() or None,
                "date_added": row.get("date_added", "").strip() or None,
                "notes": row.get("notes", "").strip() or None,
            })
    return items


def all_tickers() -> list[str]:
    """Returns deduplicated list of all tickers across portfolio + watchlist."""
    tickers = set()
    for h in read_portfolio():
        tickers.add(h["ticker"])
    for w in read_watchlist():
        tickers.add(w["ticker"])
    return sorted(tickers)
