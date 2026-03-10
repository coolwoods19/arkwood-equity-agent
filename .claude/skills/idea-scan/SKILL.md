---
name: idea-scan
description: >
  Screen the watchlist for new disruptive investment ideas and ARKWOOD-fit candidates.
  Use this skill when the user asks "what should I add to the watchlist", "any new ideas
  in [sector]", "scan for genomics plays", "find the best AI infrastructure names on my
  watchlist", "what's interesting in [theme] right now", or any request to identify
  high-conviction candidates from the watchlist universe.
---

# ARKWOOD Idea Scan

Screens `data/watchlist.csv` for high-fit ARKWOOD investment candidates.
The candidate universe is **watchlist.csv only** — no improvised or hallucinated tickers.

---

## Step 1: Read Inputs

Read `data/watchlist.csv` and `data/portfolio.csv`.

Extract from the user's message:
- **Target sector(s):** specific ARKWOOD sector, or "all"
- **Constraints:** market cap, geography, "not already held", priority level
- **Number of ideas wanted:** default 5

Filter watchlist.csv:
- If a sector is specified, filter by the `sector` column
- Exclude tickers already present in portfolio.csv (unless user says otherwise)

If the filtered watchlist is empty, tell the user:
> "No matching candidates found in watchlist.csv for [sector]. Please add candidates to watchlist.csv first, then re-run /idea-scan."

Do not proceed further if the watchlist yields no matches.

---

## Step 2: Present Candidates

Show the user the filtered watchlist entries (ticker, sector, why_watching, priority, target_entry). Ask which to analyze in depth — limit to **3 tickers at a time** to keep output manageable.

```
Here are the watchlist candidates matching your criteria:

| Ticker | Sector | Why Watching | Priority | Target Entry |
|--------|--------|-------------|---------|-------------|
| ...    | ...    | ...         | ...     | ...         |

Which would you like me to analyze? (Choose up to 3)
```

---

## Step 3: Fetch Data for Selected Tickers

```bash
python3 scripts/fetch_market_data.py {SELECTED_TICKERS} > /tmp/arkwood_scan_market.json
python3 scripts/fetch_fundamentals.py {SELECTED_TICKERS} > /tmp/arkwood_scan_fundamentals.json
python3 scripts/fetch_ark_holdings.py {SELECTED_TICKERS} > /tmp/arkwood_scan_ark.json
python3 scripts/fetch_news.py {SELECTED_TICKERS} > /tmp/arkwood_scan_news.json
python3 scripts/merge_data.py \
  /tmp/arkwood_scan_market.json \
  /tmp/arkwood_scan_fundamentals.json \
  /tmp/arkwood_scan_ark.json \
  /tmp/arkwood_scan_news.json > /tmp/arkwood_scan_merged.json
python3 scripts/compute_scores.py /tmp/arkwood_scan_merged.json > /tmp/arkwood_scan_scores.json
```

---

## Step 4: Write Condensed Analysis

For each selected ticker, write a **condensed analysis** (not the full 11-section deep dive). Include only:

**Section 1 — Company Overview**
What it does, business model, TAM, drives vs leverages disruption.

**Section 2 — Technology & Innovation Position**
Moat, adoption stage, convergence map, Wright's Law applicability.

**Section 4 — Financial Health**
Revenue scale, growth rate, margins, cash position. Flag if pre-revenue or loss-making with runway < 12 months.

**Section 5 — Valuation**
Forward P/E, PEG estimate, upside to consensus. Cheap / Fair / Expensive call.

**Section 7 — ARK Alignment**
ARK ETF exposure and conviction level.

**Section 10 — Asymmetric Upside**
5-year bull case and downside risks.

**TVS Score (abbreviated):**
Show auto_total and key manual scores. Full breakdown not required.

---

## Step 5: Watchlist Recommendation

End each ticker analysis with:

**Watchlist Recommendation: STRONG ADD / ADD / MONITOR / PASS**
- **STRONG ADD:** TVS auto_total ≥ 30, strong innovation fit, current price at or below target_entry in watchlist.csv
- **ADD:** TVS auto_total 20–29, good fit, within 10% of target_entry
- **MONITOR:** Good thesis but expensive or waiting for a catalyst
- **PASS:** Weak ARKWOOD fit, poor fundamentals, or fragility flags

**Suggested entry price range:** Based on upside_to_consensus and analyst targets.
e.g., "Entry range: $X – $Y (consensus target implies X% upside from current price)"

---

## Step 6: Save Report

```bash
# Write report to: reports/{YYYYMMDD}_idea_scan_{SECTOR}.md
```

---

## Step 7: Propose Watchlist Updates (Optional)

If any PASS candidates appear significantly misfit for the watchlist, suggest:
> "Consider removing {TICKER} from watchlist.csv — [reason]. Would you like to update the file?"

**Never auto-edit watchlist.csv or portfolio.csv.** User confirms all changes.
