"""
fetch_fundamentals.py — ARKWOOD FIU
Fetches income statement, balance sheet, cash flow, and consensus data via yfinance.

Usage:
    python3 scripts/fetch_fundamentals.py TSLA NVDA

Output: JSON to stdout

Notes:
- All fields are best-effort. Missing fields are logged in missing_fields[], not raised as errors.
- peg_estimate uses yfinance trailing earningsGrowth — treat as indicative only.
- Consensus targets (targetMeanPrice etc.) may be stale or absent for small-caps.
"""

import sys
import json
import time
from datetime import datetime, timezone

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    print(json.dumps({"error": "Missing deps. Run: pip3 install yfinance pandas"}))
    sys.exit(1)


def safe_float(val, missing_list, key):
    try:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            missing_list.append(key)
            return None
        return float(val)
    except Exception:
        missing_list.append(key)
        return None


def gross_margin_trend(financials_df) -> str:
    """Returns 'expanding', 'contracting', or 'flat' based on last 3 years of gross margin."""
    try:
        if financials_df is None or financials_df.empty:
            return None
        revenue_row = None
        gross_row = None
        for label in financials_df.index:
            if "total revenue" in label.lower():
                revenue_row = financials_df.loc[label]
            if "gross profit" in label.lower():
                gross_row = financials_df.loc[label]
        if revenue_row is None or gross_row is None:
            return None
        margins = []
        for col in financials_df.columns[:3]:
            rev = revenue_row.get(col)
            gp = gross_row.get(col)
            if rev and gp and float(rev) != 0:
                margins.append(float(gp) / float(rev))
        if len(margins) < 2:
            return None
        delta = margins[0] - margins[-1]  # most recent vs oldest
        if delta > 0.02:
            return "expanding"
        elif delta < -0.02:
            return "contracting"
        return "flat"
    except Exception:
        return None


def revenue_cagr(financials_df, years=3) -> float:
    """Compute revenue CAGR over available years."""
    try:
        if financials_df is None or financials_df.empty:
            return None
        for label in financials_df.index:
            if "total revenue" in label.lower():
                row = financials_df.loc[label].dropna()
                vals = [float(v) for v in row.values if v]
                if len(vals) < 2:
                    return None
                newest, oldest = vals[0], vals[-1]
                n = len(vals) - 1
                if oldest <= 0:
                    return None
                return round((newest / oldest) ** (1 / n) - 1, 4)
        return None
    except Exception:
        return None


def fetch_ticker(symbol: str) -> dict:
    missing = []
    data = {}

    try:
        tk = yf.Ticker(symbol)
        info = tk.info or {}

        def get(key):
            val = info.get(key)
            if val is None:
                missing.append(key)
            return val

        # Valuation multiples
        trailing_pe = safe_float(get("trailingPE"), missing, "trailingPE_safe")
        forward_pe = safe_float(get("forwardPE"), missing, "forwardPE_safe")
        price_to_book = safe_float(get("priceToBook"), missing, "priceToBook_safe")
        ev_to_ebitda = safe_float(get("enterpriseToEbitda"), missing, "enterpriseToEbitda_safe")

        # Growth & margins
        revenue_growth_yoy = safe_float(get("revenueGrowth"), missing, "revenueGrowth_safe")
        gross_margins = safe_float(get("grossMargins"), missing, "grossMargins_safe")
        operating_margins = safe_float(get("operatingMargins"), missing, "operatingMargins_safe")
        earnings_growth = safe_float(get("earningsGrowth"), missing, "earningsGrowth_safe")
        roe = safe_float(get("returnOnEquity"), missing, "returnOnEquity_safe")

        # Balance sheet
        total_debt = safe_float(get("totalDebt"), missing, "totalDebt_safe")
        total_cash = safe_float(get("totalCash"), missing, "totalCash_safe")
        fcf = safe_float(get("freeCashflow"), missing, "freeCashflow_safe")

        # Consensus / analyst targets
        target_mean = safe_float(get("targetMeanPrice"), missing, "targetMeanPrice_safe")
        target_high = safe_float(get("targetHighPrice"), missing, "targetHighPrice_safe")
        target_low = safe_float(get("targetLowPrice"), missing, "targetLowPrice_safe")
        analyst_count = info.get("numberOfAnalystOpinions")
        if analyst_count is None:
            missing.append("numberOfAnalystOpinions")
        recommendation_key = info.get("recommendationKey")
        if recommendation_key is None:
            missing.append("recommendationKey")

        current_price = info.get("currentPrice") or info.get("regularMarketPrice")

        # Derived fields
        cash_runway_months = None
        if fcf is not None and fcf < 0 and total_cash is not None:
            monthly_burn = abs(fcf) / 12
            cash_runway_months = round(total_cash / monthly_burn, 1) if monthly_burn else None
        elif fcf is not None and fcf >= 0:
            cash_runway_months = "profitable"

        upside_to_consensus = None
        if target_mean and current_price and current_price > 0:
            upside_to_consensus = round((target_mean - current_price) / current_price, 4)

        peg_estimate = None
        peg_note = None
        if forward_pe and earnings_growth and earnings_growth > 0:
            peg_estimate = round(forward_pe / (earnings_growth * 100), 3)
            peg_note = "uses yfinance trailing earningsGrowth — treat as indicative only"
        else:
            missing.append("peg_estimate")

        # Multi-year financials
        try:
            fin = tk.financials
            gm_trend = gross_margin_trend(fin)
            rev_cagr = revenue_cagr(fin)
        except Exception:
            fin = None
            gm_trend = None
            rev_cagr = None
            missing.append("financials_history")

        data = {
            "trailing_pe": trailing_pe,
            "forward_pe": forward_pe,
            "price_to_book": price_to_book,
            "ev_to_ebitda": ev_to_ebitda,
            "revenue_growth_yoy": revenue_growth_yoy,
            "revenue_cagr_3y": rev_cagr,
            "gross_margin": gross_margins,
            "gross_margin_trend": gm_trend,
            "operating_margin": operating_margins,
            "earnings_growth": earnings_growth,
            "roe": roe,
            "total_debt": total_debt,
            "total_cash": total_cash,
            "free_cash_flow": fcf,
            "cash_runway_months": cash_runway_months,
            "target_mean_price": target_mean,
            "target_high_price": target_high,
            "target_low_price": target_low,
            "analyst_count": analyst_count,
            "recommendation_key": recommendation_key,
            "upside_to_consensus": upside_to_consensus,
            "peg_estimate": peg_estimate,
            "_notes": {
                "peg_estimate": peg_note,
                "consensus_targets": "may be stale or absent for small-caps",
            },
        }

        quality = "FULL" if len(missing) == 0 else ("PARTIAL" if len(missing) < 8 else "EMPTY")
        return {"data_quality": quality, "missing_fields": list(set(missing)), **data}

    except Exception as e:
        return {
            "data_quality": "EMPTY",
            "missing_fields": ["all"],
            "error": str(e),
        }


def main():
    tickers = [t.upper() for t in sys.argv[1:]]
    if not tickers:
        print(json.dumps({"error": "No tickers provided. Usage: fetch_fundamentals.py TSLA NVDA"}))
        sys.exit(1)

    results = {}
    for i, symbol in enumerate(tickers):
        results[symbol] = fetch_ticker(symbol)
        if i < len(tickers) - 1:
            time.sleep(0.5)

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "as_of": "trailing-12m",
        "tickers": results,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
