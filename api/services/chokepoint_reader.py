"""
chokepoint_reader.py - ARKWOOD FIU
Reads structured AI chokepoint profiles and derives the two-axis overlay.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


DATA_DIR = Path(__file__).parent.parent.parent / "data"
CHOKEPOINT_DIR = DATA_DIR / "chokepoints"

DURABILITY_KEYS = {
    "necessity": "Necessity for AI scaling",
    "structural_scarcity": "Structural scarcity",
    "pricing_power": "Pricing power",
    "supply_substitution_defense": "Supply response / substitution defense",
    "inference_resilience": "Inference resilience",
}

ENTRY_RISK_KEYS = {
    "capex_shock_resilience": "Capex shock resilience",
    "valuation_crowdedness": "Valuation / crowdedness",
    "concentration_idiosyncratic_risk": "Concentration / idiosyncratic risk",
}


def _score(value) -> int:
    if not isinstance(value, (int, float)):
        raise ValueError("score must be numeric")
    if value < 0 or value > 10:
        raise ValueError("score must be between 0 and 10")
    return int(value)


def _normalize_scores(raw_scores: dict, keys: dict[str, str]) -> dict[str, int]:
    return {key: _score(raw_scores.get(key, 0)) for key in keys}


def derive_durability_class(score: int) -> str:
    if score >= 45:
        return "Tier 1 Monopoly / Essential Chokepoint"
    if score >= 38:
        return "Tier 1/Tier 2 Structural Bottleneck"
    if score >= 30:
        return "Tier 2 AI Infrastructure Winner"
    if score >= 22:
        return "High-Beta AI Beneficiary"
    return "Weak Chokepoint"


def derive_entry_quality(score: int) -> str:
    if score >= 24:
        return "Attractive / resilient entry"
    if score >= 18:
        return "Acceptable, selective entry"
    if score >= 12:
        return "Risky or valuation-constrained"
    return "Poor entry quality"


def derive_sizing_bias(durability_score: int, entry_score: int) -> str:
    if durability_score >= 45 and entry_score >= 18:
        return "Core candidate"
    if durability_score >= 45:
        return "Core watch / add on dislocation"
    if durability_score >= 38 and entry_score >= 18:
        return "Core or satellite, selective entry"
    if durability_score >= 30 and entry_score >= 18:
        return "Satellite add candidate"
    if durability_score >= 30:
        return "Satellite / tactical only"
    if durability_score >= 22:
        return "Watchlist / tactical"
    return "Avoid as core"


def derive_assessment_mode(durability_score: int, explicit_mode: Optional[str]) -> str:
    if explicit_mode:
        return explicit_mode
    if durability_score >= 38:
        return "Infrastructure Chokepoint"
    if durability_score >= 30:
        return "Hybrid AI Infrastructure Winner"
    return "AI Beneficiary"


def build_chokepoint_overlay(profile: dict) -> dict:
    scores = profile.get("scores") or {}
    durability_scores = _normalize_scores(scores.get("durability") or {}, DURABILITY_KEYS)
    entry_scores = _normalize_scores(scores.get("entry_risk") or {}, ENTRY_RISK_KEYS)

    durability_total = sum(durability_scores.values())
    entry_total = sum(entry_scores.values())

    return {
        "ticker": (profile.get("ticker") or "").upper(),
        "ai_role": profile.get("ai_role"),
        "assessment_mode": derive_assessment_mode(
            durability_total, profile.get("assessment_mode")
        ),
        "durability": {
            "score": durability_total,
            "max_score": 50,
            "classification": derive_durability_class(durability_total),
            "scores": durability_scores,
            "labels": DURABILITY_KEYS,
        },
        "entry_risk": {
            "score": entry_total,
            "max_score": 30,
            "classification": derive_entry_quality(entry_total),
            "scores": entry_scores,
            "labels": ENTRY_RISK_KEYS,
        },
        "risk_locations": profile.get("risk_locations") or [],
        "sizing_bias": profile.get("sizing_bias")
        or derive_sizing_bias(durability_total, entry_total),
        "tvs_tiebreaker": profile.get("tvs_tiebreaker"),
        "technical_timing_rule": profile.get("technical_timing_rule"),
        "rationale": profile.get("rationale"),
        "last_reviewed": profile.get("last_reviewed"),
        "data_quality": profile.get("data_quality", "MANUAL"),
    }


def read_chokepoint_profile(ticker: str) -> Optional[dict]:
    path = CHOKEPOINT_DIR / f"{ticker.upper()}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        profile = json.load(f)
    return build_chokepoint_overlay(profile)
