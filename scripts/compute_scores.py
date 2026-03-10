"""
compute_scores.py — ARKWOOD FIU
Deterministic Technology-Valuation Score (TVS) calculator (0-125).

Scores the mechanically computable criteria from merged data.
Qualitative criteria are set to null for Claude to evaluate in the skill.

Usage:
    python3 scripts/compute_scores.py merged.json > scores.json

TVS Rubric:
    A. Growth & Innovation (max 70)
       +10  Revenue growth >20% YoY                [AUTO]
       +10  Clear tech moat / niche leader          [MANUAL — Claude]
       +10  Steep S-curve (rapid adoption)          [MANUAL — Claude]
       +10  Expanding gross margins                 [AUTO]
       +10  Wright's Law / learning curve           [MANUAL — Claude]
       +10  Tech convergence (4+ platforms: +10,    [MANUAL — Claude]
                              2-3: +5-7, 1: +3)
       +10  Disruption driver (vs leverager)        [MANUAL — Claude]

    B. Valuation & Fundamentals (max 40)
       +10/-10/-20  5-Year forward PEG scoring      [AUTO]
       +10  Cash runway >24m or profitable          [AUTO]
       +10  Upside to consensus target >15%         [AUTO]
       +10  Trading below 5yr/peer avg multiples    [MANUAL — Claude]

    C. Momentum & ARK Conviction (max 15)
       +5   Held by ARK with high/stable weight     [AUTO]
       +10  Positive recent news/catalyst            [AUTO — from news script]
"""

import sys
import json
from datetime import datetime, timezone


def score_peg(peg_estimate) -> tuple[int, str]:
    """Returns (score, rationale) for PEG-based valuation."""
    if peg_estimate is None:
        return 0, "PEG unavailable — scored 0 (conservative)"
    if peg_estimate < 1.0:
        return 10, f"PEG {peg_estimate:.2f} < 1.0 — undervalued vs growth"
    elif peg_estimate <= 2.0:
        return 0, f"PEG {peg_estimate:.2f} in 1.0–2.0 range — fair value"
    elif peg_estimate <= 2.5:
        return -10, f"PEG {peg_estimate:.2f} in 2.0–2.5 range — expensive"
    else:
        return -20, f"PEG {peg_estimate:.2f} > 2.5 — very expensive"


def score_ark_conviction(conviction_level: str) -> tuple[int, str]:
    mapping = {
        "HIGH": (5, "ARK conviction HIGH (≥5% weight)"),
        "MEDIUM": (3, "ARK conviction MEDIUM (2–5% weight)"),
        "LOW": (1, "ARK conviction LOW (>0% weight)"),
        "NONE": (0, "Not held by ARK"),
    }
    return mapping.get(conviction_level, (0, "ARK conviction unknown"))


EXTENDED_SMA50_THRESHOLD = 0.15  # >15% above SMA50 triggers EXTENDED overlay


def compute_technical_overlay(technicals: dict) -> dict:
    """
    Computes the technical overlay from a single ticker's technicals sub-dict.
    Returns overlay dict with signals, bullish/bearish counts, overlay_rating, and notes.
    overlay_rating priority (first match wins):
        1. EXTENDED:     momentum == OVERBOUGHT OR price_vs_sma50_pct > 0.15
        2. AVOID:        bearish_count >= 2
        3. STRONG_SETUP: bullish_count >= 3 AND bearish_count == 0
        4. SETUP:        bullish_count >= 2 AND bearish_count <= 1
        5. NEUTRAL:      all other cases
    """
    trend = technicals.get("trend_signal", "FLAT")
    momentum = technicals.get("momentum_signal", "NEUTRAL")
    breakout = technicals.get("breakout_signal", "RANGE")
    rs = technicals.get("rs_signal", "IN_LINE")
    price_vs_sma50_pct = technicals.get("price_vs_sma50_pct")
    rsi_14 = technicals.get("rsi_14")

    signals = {
        "trend": trend,
        "momentum": momentum,
        "breakout": breakout,
        "relative_strength": rs,
    }

    bullish_signals = []
    bearish_signals = []

    if trend == "UPTREND":
        bullish_signals.append("trend")
    elif trend == "DOWNTREND":
        bearish_signals.append("trend")

    if momentum == "BULLISH":
        bullish_signals.append("momentum")
    elif momentum in ("OVERBOUGHT", "OVERSOLD"):
        bearish_signals.append("momentum")

    if breakout == "BREAKING_OUT":
        bullish_signals.append("breakout")
    elif breakout == "BREAKING_DOWN":
        bearish_signals.append("breakout")

    if rs == "LEADING":
        bullish_signals.append("relative_strength")
    elif rs == "LAGGING":
        bearish_signals.append("relative_strength")

    bullish_count = len(bullish_signals)
    bearish_count = len(bearish_signals)

    # Determine overlay_rating (first match wins)
    extended_by_rsi = momentum == "OVERBOUGHT"
    extended_by_sma = price_vs_sma50_pct is not None and price_vs_sma50_pct > EXTENDED_SMA50_THRESHOLD

    if extended_by_rsi or extended_by_sma:
        overlay_rating = "EXTENDED"
    elif bearish_count >= 2:
        overlay_rating = "AVOID"
    elif bullish_count >= 3 and bearish_count == 0:
        overlay_rating = "STRONG_SETUP"
    elif bullish_count >= 2 and bearish_count <= 1:
        overlay_rating = "SETUP"
    else:
        overlay_rating = "NEUTRAL"

    return {
        "signals": signals,
        "bullish_signals": bullish_signals,
        "bearish_signals": bearish_signals,
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "overlay_rating": overlay_rating,
        "overlay_notes": {
            "rsi_14": rsi_14,
            "price_vs_sma50_pct": price_vs_sma50_pct,
            "sma_50": technicals.get("sma_50"),
            "sma_200": technicals.get("sma_200"),
            "price_vs_52w_high_pct": technicals.get("price_vs_52w_high_pct"),
        },
    }


def score_ticker(ticker: str, data: dict) -> dict:
    market = data.get("market", {})
    fundamentals = data.get("fundamentals", {})
    ark = data.get("ark", {})
    news = data.get("news", {})

    notes = {}
    auto_scores = {}

    # --- Section A: Growth & Innovation (auto-scoreable items) ---

    # Revenue growth >20% YoY
    rev_growth = fundamentals.get("revenue_growth_yoy")
    if rev_growth is not None:
        auto_scores["revenue_growth_over_20pct"] = 10 if rev_growth > 0.20 else 0
        notes["revenue_growth_yoy"] = f"{rev_growth:.1%}"
    else:
        auto_scores["revenue_growth_over_20pct"] = 0
        notes["revenue_growth_yoy"] = "unavailable — scored 0 (conservative)"

    # Expanding gross margins
    gm_trend = fundamentals.get("gross_margin_trend")
    if gm_trend == "expanding":
        auto_scores["expanding_gross_margins"] = 10
    else:
        auto_scores["expanding_gross_margins"] = 0
    notes["gross_margin_trend"] = gm_trend or "unavailable"

    # --- Section B: Valuation & Fundamentals ---

    # PEG scoring
    peg = fundamentals.get("peg_estimate")
    peg_score, peg_note = score_peg(peg)
    auto_scores["peg_score"] = peg_score
    notes["peg_estimate"] = peg_note

    # Cash runway >24 months or profitable
    runway = fundamentals.get("cash_runway_months")
    if runway == "profitable" or (isinstance(runway, (int, float)) and runway > 24):
        auto_scores["cash_runway_score"] = 10
        notes["cash_runway"] = str(runway)
    else:
        auto_scores["cash_runway_score"] = 0
        notes["cash_runway"] = str(runway) if runway is not None else "unavailable"

    # Upside to consensus >15%
    upside = fundamentals.get("upside_to_consensus")
    if upside is not None:
        auto_scores["upside_to_consensus_score"] = 10 if upside > 0.15 else 0
        notes["upside_to_consensus"] = f"{upside:.1%}"
    else:
        auto_scores["upside_to_consensus_score"] = 0
        notes["upside_to_consensus"] = "unavailable — scored 0 (conservative)"

    # --- Section C: Momentum & ARK Conviction ---

    # ARK conviction
    conviction = ark.get("conviction_level", "NONE") if not ark.get("_missing") else "NONE"
    ark_score, ark_note = score_ark_conviction(conviction)
    auto_scores["ark_conviction_score"] = ark_score
    notes["ark_conviction"] = ark_note

    # News/catalyst score
    catalyst_score = news.get("recent_catalyst_score") if not news.get("_missing") else None
    if catalyst_score is not None:
        auto_scores["news_catalyst_score"] = catalyst_score
        notes["news_catalyst"] = f"Score from news sentiment: {catalyst_score}/10"
    else:
        auto_scores["news_catalyst_score"] = 0
        notes["news_catalyst"] = "News data unavailable — scored 0"

    auto_total = sum(auto_scores.values())

    # --- Technical Overlay (separate from TVS — does not affect auto_total) ---
    technicals = data.get("technicals", {})
    technical_overlay = None
    if technicals and not technicals.get("_missing"):
        technical_overlay = compute_technical_overlay(technicals)

    return {
        "auto_scores": auto_scores,
        "auto_total": auto_total,
        "manual_scores_needed": {
            "tech_moat": None,          # 0 or 10
            "s_curve_adoption": None,   # 0 or 10
            "wrights_law": None,        # 0 or 10
            "tech_convergence": None,   # 0, 3, 5-7, or 10
            "disruption_driver": None,  # 0 or 10
            "below_5yr_peer_avg": None, # 0 or 10
        },
        "max_possible_auto": 45,   # sum of all auto-scored max values
        "max_possible_total": 125,
        "notes": notes,
        "technical_overlay": technical_overlay,
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: compute_scores.py merged.json"}))
        sys.exit(1)

    path = sys.argv[1]
    try:
        with open(path) as f:
            merged = json.load(f)
    except FileNotFoundError:
        print(json.dumps({"error": f"File not found: {path}"}))
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"JSON parse error: {e}"}))
        sys.exit(1)

    tickers_data = merged.get("tickers", {})
    scores = {}
    for ticker, data in tickers_data.items():
        scores[ticker] = score_ticker(ticker, data)

    output = {
        "scored_at": datetime.now(timezone.utc).isoformat(),
        "rubric_version": "1.1",
        "scores": scores,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
