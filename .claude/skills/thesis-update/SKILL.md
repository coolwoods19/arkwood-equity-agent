---
name: thesis-update
description: >
  Refresh and update the investment thesis document for a portfolio holding or watchlist stock.
  Use this skill when the user says "update the thesis for [TICKER]", "review my thesis on
  [TICKER]", "has the thesis changed for [TICKER]", "re-check my conviction on [TICKER]",
  or after an earnings report, major news event, large price move, or quarterly review.
---

# ARKWOOD Thesis Update

Refreshes the stored investment thesis for a ticker and flags what has changed.

---

## Step 1: Identify Ticker

Extract the ticker from the user's message. If ambiguous, ask for clarification.

---

## Step 2: Read Existing Thesis

Check if `data/thesis/{TICKER}.md` exists.

- **If yes:** Read it fully. Note the original thesis date, confidence level, key assumptions, and invalidation triggers.
- **If no:** Use `data/thesis/TEMPLATE.md` as the starting structure. State to the user: "No prior thesis found for {TICKER} — creating a new one."

---

## Step 3: Fetch Fresh Data

```bash
python3 scripts/fetch_market_data.py {TICKER} > /tmp/arkwood_thesis_market.json
python3 scripts/fetch_fundamentals.py {TICKER} > /tmp/arkwood_thesis_fundamentals.json
python3 scripts/fetch_ark_holdings.py {TICKER} > /tmp/arkwood_thesis_ark.json
python3 scripts/fetch_news.py {TICKER} > /tmp/arkwood_thesis_news.json
python3 scripts/fetch_technicals.py {TICKER} > /tmp/arkwood_thesis_technicals.json
python3 scripts/merge_data.py \
  /tmp/arkwood_thesis_market.json \
  /tmp/arkwood_thesis_fundamentals.json \
  /tmp/arkwood_thesis_ark.json \
  /tmp/arkwood_thesis_news.json \
  /tmp/arkwood_thesis_technicals.json > /tmp/arkwood_thesis_merged.json
python3 scripts/compute_scores.py /tmp/arkwood_thesis_merged.json > /tmp/arkwood_thesis_scores.json
```

---

## Step 4: Evaluate the Thesis

For each **Key Assumption** in the existing thesis:
- Is it still valid? What does current data say?
- State: CONFIRMED / WEAKENED / INVALIDATED + one sentence of evidence

For each **Thesis Invalidation Trigger**:
- Has it been hit or is it approaching?
- State: NOT HIT / APPROACHING / HIT + one sentence of evidence

Then assess:
- New TVS auto_total from scores vs prior (if prior snapshot exists in `data/snapshots/`)
- ARK conviction change (if any)
- Key news events since last review

### Technical Signal Check

Read `technical_overlay` from `/tmp/arkwood_thesis_scores.json`.

State whether technicals confirm or contradict the thesis direction:
- **Confirms thesis:** overlay is SETUP or STRONG_SETUP and trend is UPTREND
- **Neutral:** overlay is NEUTRAL or EXTENDED (extended may signal near-term risk even if thesis intact)
- **Contradicts thesis:** overlay is AVOID or trend is DOWNTREND on a conviction BUY thesis

Include one line: `Technical Overlay: {overlay_rating} ({bullish_count}/4 bullish) — {confirms/neutral/contradicts} thesis direction.`

---

## Step 5: Assign New Thesis Confidence

Based on the evaluation:
- **HIGH:** Core assumptions intact, no invalidation triggers hit or approaching, thesis strengthening
- **MEDIUM:** 1–2 assumptions weakened or uncertain, thesis intact but monitoring required
- **LOW:** Multiple assumptions weakened, 1+ triggers approaching, thesis under significant pressure

---

## Step 6: Write Updated Thesis

Write the updated `data/thesis/{TICKER}.md` using the TEMPLATE structure:

1. Update the date, confidence level, and TVS score header
2. Revise the Core Thesis Statement if the narrative has shifted
3. Update Key Assumptions (mark changed ones with `[UPDATED]`)
4. Update Invalidation Triggers (mark triggered or approaching ones)
5. Update Milestones to Watch (mark completed milestones, add new ones)
6. Update the ARK-Fit Summary if convergence or leadership has changed
7. **Append a new row** to the Revision History table — never delete prior rows

---

## Step 7: Present Summary to User

Present a change summary:

```
## Thesis Update Summary — {TICKER}

**Prior confidence:** {OLD} → **New confidence:** {NEW}
**TVS auto_total:** {PRIOR} → {CURRENT} (delta: {+/-X})

### What Changed
- [Assumption 1]: CONFIRMED / WEAKENED / INVALIDATED — [evidence]
- [Assumption 2]: ...

### Invalidation Trigger Status
- [Trigger 1]: NOT HIT / APPROACHING / HIT — [evidence]

### Key New Developments
- [Top news items or data changes since last review]

### Recommended Action
[HOLD thesis / INCREASE conviction / REDUCE conviction / EXIT — one sentence rationale]
```

---

## Step 8: Recommend portfolio.csv Update

If thesis_confidence has changed, tell the user:

"I recommend updating `thesis_confidence` for {TICKER} from `{OLD}` to `{NEW}` in `portfolio.csv`, and setting `last_reviewed` to today's date. Would you like to make this change?"

**Never auto-edit portfolio.csv.** Wait for explicit user confirmation before any changes.
