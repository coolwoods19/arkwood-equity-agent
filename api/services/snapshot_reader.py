"""
snapshot_reader.py — ARKWOOD FIU
Finds the latest snapshot JSONs and merges them into API response shapes.
Rating logic lives here — frontend receives a string, never computes it.
"""

import json
from pathlib import Path
from typing import Optional
from datetime import date, datetime

DATA_DIR = Path(__file__).parent.parent.parent / "data"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"


# ---------------------------------------------------------------------------
# Rating derivation (backend-only)
# ---------------------------------------------------------------------------

def derive_rating(auto_total: Optional[int], overlay_rating: Optional[str]) -> Optional[str]:
    if auto_total is None:
        return None
    overlay = overlay_rating or "NEUTRAL"
    if auto_total >= 40 and overlay in ("STRONG_SETUP", "SETUP"):
        return "STRONG BUY"
    if auto_total >= 30 and overlay != "AVOID":
        return "BUY"
    if auto_total >= 20:
        return "HOLD"
    return "SELL"


# ---------------------------------------------------------------------------
# Snapshot file discovery
# ---------------------------------------------------------------------------

def _latest_snapshot_file(pattern: str) -> Optional[Path]:
    """Returns the most recent file matching a glob pattern (YYYYMMDD prefix sorts correctly)."""
    matches = sorted(SNAPSHOTS_DIR.glob(pattern))
    return matches[-1] if matches else None


def get_latest_portfolio_snapshot() -> Optional[dict]:
    path = _latest_snapshot_file("*_portfolio_snapshot.json")
    if not path:
        return None
    with open(path) as f:
        return json.load(f)


def get_latest_portfolio_scores() -> Optional[dict]:
    path = _latest_snapshot_file("*_portfolio_scores.json")
    if not path:
        return None
    with open(path) as f:
        return json.load(f)


def get_latest_snapshot_date() -> Optional[str]:
    path = _latest_snapshot_file("*_portfolio_snapshot.json")
    if not path:
        return None
    # filename is YYYYMMDD_portfolio_snapshot.json
    stem = path.stem  # e.g. "20260310_portfolio_snapshot"
    date_part = stem.split("_")[0]  # "20260310"
    try:
        return datetime.strptime(date_part, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        return None


def snapshot_days_old() -> Optional[int]:
    snap_date_str = get_latest_snapshot_date()
    if not snap_date_str:
        return None
    snap_date = datetime.strptime(snap_date_str, "%Y-%m-%d").date()
    return (date.today() - snap_date).days


# ---------------------------------------------------------------------------
# Alert evaluation
# ---------------------------------------------------------------------------

def _check_alert(current_price: Optional[float], alert_below: Optional[float], alert_above: Optional[float]) -> tuple[bool, Optional[str]]:
    if current_price is None:
        return False, None
    if alert_below is not None and current_price < alert_below:
        return True, "BELOW"
    if alert_above is not None and current_price > alert_above:
        return True, "ABOVE"
    return False, None


# ---------------------------------------------------------------------------
# Public API: portfolio summary
# ---------------------------------------------------------------------------

def build_portfolio_response(holdings_csv: list[dict]) -> dict:
    snapshot = get_latest_portfolio_snapshot() or {}
    scores_data = get_latest_portfolio_scores() or {}

    snap_tickers: dict = snapshot.get("tickers", {})
    scores_map: dict = scores_data.get("scores", {})

    snapshot_date = get_latest_snapshot_date()
    days_old = snapshot_days_old()

    result_holdings = []
    total_market_value = 0.0
    total_cost_basis = 0.0
    active_alerts = 0

    for h in holdings_csv:
        ticker = h["ticker"]
        snap = snap_tickers.get(ticker, {})
        score = scores_map.get(ticker, {})

        market = snap.get("market", {})
        current_price: Optional[float] = market.get("current_price")
        short_name: Optional[str] = market.get("short_name")

        shares = h.get("shares") or 0.0
        avg_cost = h.get("avg_cost") or 0.0

        market_value = round(shares * current_price, 2) if current_price is not None else None
        unrealized_pnl = round((current_price - avg_cost) * shares, 2) if current_price is not None else None
        unrealized_pnl_pct = round((current_price - avg_cost) / avg_cost, 6) if current_price is not None and avg_cost else None

        if market_value is not None:
            total_market_value += market_value
            total_cost_basis += shares * avg_cost

        alert_triggered, alert_direction = _check_alert(
            current_price, h.get("alert_below"), h.get("alert_above")
        )
        if alert_triggered:
            active_alerts += 1

        overlay = score.get("technical_overlay") or {}
        overlay_rating = overlay.get("overlay_rating")
        auto_total = score.get("auto_total")

        # Determine data quality (minimum across market + fundamentals + technicals)
        qualities = [
            snap.get("market", {}).get("data_quality"),
            snap.get("fundamentals", {}).get("data_quality"),
            snap.get("technicals", {}).get("data_quality"),
        ]
        quality_rank = {"FULL": 3, "PARTIAL": 2, "EMPTY": 1, "UNKNOWN": 0, None: 0}
        data_quality = min((q for q in qualities if q), key=lambda q: quality_rank.get(q, 0), default="EMPTY")

        thesis_file = DATA_DIR / "thesis" / f"{ticker}.md"

        result_holdings.append({
            "ticker": ticker,
            "short_name": short_name,
            "shares": h.get("shares"),
            "avg_cost": h.get("avg_cost"),
            "current_price": current_price,
            "market_value": market_value,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_pct": unrealized_pnl_pct,
            "target_weight": h.get("target_weight"),
            "max_weight": h.get("max_weight"),
            "alert_below": h.get("alert_below"),
            "alert_above": h.get("alert_above"),
            "alert_triggered": alert_triggered,
            "alert_direction": alert_direction,
            "sector": h.get("sector"),
            "thesis_confidence": h.get("thesis_confidence"),
            "last_reviewed": h.get("last_reviewed"),
            "overlay_rating": overlay_rating,
            "auto_total": auto_total,
            "rating": derive_rating(auto_total, overlay_rating),
            "data_quality": data_quality,
            "has_thesis": thesis_file.exists(),
        })

    total_unrealized_pnl = round(total_market_value - total_cost_basis, 2) if total_market_value else None
    total_unrealized_pnl_pct = round((total_market_value - total_cost_basis) / total_cost_basis, 6) if total_cost_basis else None

    return {
        "snapshot_date": snapshot_date,
        "snapshot_days_old": days_old,
        "holdings": result_holdings,
        "portfolio_totals": {
            "total_market_value": round(total_market_value, 2),
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_unrealized_pnl_pct": total_unrealized_pnl_pct,
            "active_alerts": active_alerts,
        },
    }


# ---------------------------------------------------------------------------
# Public API: single ticker detail
# ---------------------------------------------------------------------------

def build_ticker_detail(ticker: str, holding_csv: Optional[dict], watchlist_csv: Optional[dict]) -> dict:
    snapshot = get_latest_portfolio_snapshot() or {}
    scores_data = get_latest_portfolio_scores() or {}

    snap_tickers = snapshot.get("tickers", {})
    scores_map = scores_data.get("scores", {})

    snap = snap_tickers.get(ticker, {})
    score = scores_map.get(ticker, {})

    market_raw = snap.get("market", {}) or {}
    fundamentals_raw = snap.get("fundamentals", {}) or {}
    technicals_raw = snap.get("technicals", {}) or {}
    ark_raw = snap.get("ark", {}) or {}
    news_raw = snap.get("news", {}) or {}

    # Skip internal _missing sentinel
    def clean(d: dict) -> dict:
        if d.get("_missing"):
            return {}
        return d

    market_raw = clean(market_raw)
    fundamentals_raw = clean(fundamentals_raw)
    technicals_raw = clean(technicals_raw)
    ark_raw = clean(ark_raw)
    news_raw = clean(news_raw)

    overlay = score.get("technical_overlay") or {}
    overlay_rating = overlay.get("overlay_rating")
    auto_total = score.get("auto_total")

    qualities = [
        market_raw.get("data_quality"),
        fundamentals_raw.get("data_quality"),
        technicals_raw.get("data_quality"),
    ]
    quality_rank = {"FULL": 3, "PARTIAL": 2, "EMPTY": 1, "UNKNOWN": 0}
    data_quality = min((q for q in qualities if q in quality_rank), key=lambda q: quality_rank[q], default="EMPTY")

    # Thesis
    thesis_path = DATA_DIR / "thesis" / f"{ticker}.md"
    thesis_markdown: Optional[str] = thesis_path.read_text() if thesis_path.exists() else None

    # Holding info (null for watchlist-only)
    holding_out: Optional[dict] = None
    if holding_csv:
        h = holding_csv
        holding_out = {
            "shares": h.get("shares"),
            "avg_cost": h.get("avg_cost"),
            "thesis_confidence": h.get("thesis_confidence"),
            "last_reviewed": h.get("last_reviewed"),
            "alert_below": h.get("alert_below"),
            "alert_above": h.get("alert_above"),
        }

    return {
        "ticker": ticker,
        "snapshot_date": get_latest_snapshot_date(),
        "rating": derive_rating(auto_total, overlay_rating),
        "data_quality": data_quality,
        "market": {
            "current_price": market_raw.get("current_price"),
            "market_cap": market_raw.get("market_cap"),
            "beta": market_raw.get("beta"),
            "fifty_two_week_high": market_raw.get("fifty_two_week_high"),
            "fifty_two_week_low": market_raw.get("fifty_two_week_low"),
            "ytd_return": market_raw.get("ytd_return"),
            "sector": market_raw.get("sector"),
            "industry": market_raw.get("industry"),
            "price_history_30d": market_raw.get("price_history_30d") or [],
            "data_quality": market_raw.get("data_quality", "EMPTY"),
            "missing_fields": market_raw.get("missing_fields") or [],
        },
        "fundamentals": {
            "trailing_pe": fundamentals_raw.get("trailing_pe"),
            "forward_pe": fundamentals_raw.get("forward_pe"),
            "revenue_growth_yoy": fundamentals_raw.get("revenue_growth_yoy"),
            "gross_margin": fundamentals_raw.get("gross_margin"),
            "gross_margin_trend": fundamentals_raw.get("gross_margin_trend"),
            "operating_margin": fundamentals_raw.get("operating_margin"),
            "upside_to_consensus": fundamentals_raw.get("upside_to_consensus"),
            "target_mean_price": fundamentals_raw.get("target_mean_price"),
            "analyst_count": fundamentals_raw.get("analyst_count"),
            "cash_runway_months": fundamentals_raw.get("cash_runway_months"),
            "peg_estimate": fundamentals_raw.get("peg_estimate"),
            "data_quality": fundamentals_raw.get("data_quality", "EMPTY"),
            "missing_fields": fundamentals_raw.get("missing_fields") or [],
        },
        "technicals": {
            "sma_50": technicals_raw.get("sma_50"),
            "sma_200": technicals_raw.get("sma_200"),
            "rsi_14": technicals_raw.get("rsi_14"),
            "trend_signal": technicals_raw.get("trend_signal"),
            "momentum_signal": technicals_raw.get("momentum_signal"),
            "breakout_signal": technicals_raw.get("breakout_signal"),
            "rs_signal": technicals_raw.get("rs_signal"),
            "price_vs_sma50_pct": technicals_raw.get("price_vs_sma50_pct"),
            "return_1m": technicals_raw.get("return_1m"),
            "return_3m": technicals_raw.get("return_3m"),
            "data_quality": technicals_raw.get("data_quality", "EMPTY"),
            "missing_fields": technicals_raw.get("missing_fields") or [],
        },
        "scores": {
            "auto_scores": score.get("auto_scores") or {},
            "auto_total": auto_total,
            "max_possible_auto": score.get("max_possible_auto", 45),
            "max_possible_total": score.get("max_possible_total", 125),
            "manual_scores_needed": score.get("manual_scores_needed") or {},
            "notes": score.get("notes") or {},
            "technical_overlay": {
                "overlay_rating": overlay_rating,
                "bullish_signals": overlay.get("bullish_signals") or [],
                "bearish_signals": overlay.get("bearish_signals") or [],
                "bullish_count": overlay.get("bullish_count", 0),
                "bearish_count": overlay.get("bearish_count", 0),
                "overlay_notes": overlay.get("overlay_notes") or {},
            } if overlay else None,
        },
        "ark": {
            "ark_held": ark_raw.get("ark_held", False),
            "conviction_level": ark_raw.get("conviction_level", "NONE"),
            "total_etfs_held_in": ark_raw.get("total_etfs_held_in", 0),
            "holdings": ark_raw.get("holdings") or [],
        },
        "news": {
            "article_count": news_raw.get("article_count", 0),
            "recent_catalyst_score": news_raw.get("recent_catalyst_score", 0),
            "articles": news_raw.get("articles") or [],
            "data_quality": news_raw.get("data_quality", "EMPTY"),
        },
        "holding": holding_out,
        "thesis_markdown": thesis_markdown,
    }
