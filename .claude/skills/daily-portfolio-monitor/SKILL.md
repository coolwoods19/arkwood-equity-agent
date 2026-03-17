---
name: daily-portfolio-monitor
description: >
  Run the ARKWOOD daily portfolio sweep. Reads all positions from portfolio.csv, fetches
  live market data, scores each holding, checks price alerts, compares to prior snapshots,
  and produces a morning briefing report with Telegram notification. Use this skill when
  the user says "run the daily monitor", "morning briefing", "check the portfolio",
  "what's the portfolio looking like today", or when invoked by the external cron job.
---

# ARKWOOD Daily Portfolio Monitor

Produces a complete morning portfolio briefing. Execute all steps sequentially.
**Never modify portfolio.csv.**

---

## Step 1: Read Portfolio

Read `data/portfolio.csv`. Extract all tickers into a list. Also read `data/watchlist.csv` for the Watchlist Pulse section.

---

## Step 2: Fetch All Data

Run scripts sequentially. If a script fails (non-zero exit or error JSON), note the failure and continue — do not abort the run.

**Portfolio tickers:**
```bash
python3 scripts/fetch_market_data.py {TICKER_LIST} > /tmp/arkwood_daily_market.json
python3 scripts/fetch_fundamentals.py {TICKER_LIST} > /tmp/arkwood_daily_fundamentals.json
python3 scripts/fetch_ark_holdings.py {TICKER_LIST} > /tmp/arkwood_daily_ark.json
python3 scripts/fetch_news.py {TICKER_LIST} > /tmp/arkwood_daily_news.json
python3 scripts/fetch_technicals.py {TICKER_LIST} > /tmp/arkwood_daily_technicals.json
python3 scripts/merge_data.py \
  /tmp/arkwood_daily_market.json \
  /tmp/arkwood_daily_fundamentals.json \
  /tmp/arkwood_daily_ark.json \
  /tmp/arkwood_daily_news.json \
  /tmp/arkwood_daily_technicals.json > /tmp/arkwood_daily_merged.json
python3 scripts/compute_scores.py /tmp/arkwood_daily_merged.json \
  --portfolio data/portfolio.csv \
  --prior data/snapshots/{MOST_RECENT_YYYYMMDD}_portfolio_scores.json \
  > /tmp/arkwood_daily_scores.json
```

Replace `{MOST_RECENT_YYYYMMDD}` with the date of the most recent `YYYYMMDD_portfolio_scores.json` in `data/snapshots/` (ls sorted descending). If no prior snapshot exists, omit the `--prior` flag.

**Watchlist tickers** (run separately — use {WATCHLIST_TICKER_LIST} from watchlist.csv):
```bash
python3 scripts/fetch_market_data.py {WATCHLIST_TICKER_LIST} > /tmp/arkwood_wl_market.json
python3 scripts/fetch_fundamentals.py {WATCHLIST_TICKER_LIST} > /tmp/arkwood_wl_fundamentals.json
python3 scripts/fetch_technicals.py {WATCHLIST_TICKER_LIST} > /tmp/arkwood_wl_technicals.json
python3 scripts/merge_data.py \
  /tmp/arkwood_wl_market.json \
  /tmp/arkwood_wl_fundamentals.json \
  /tmp/arkwood_wl_technicals.json > /tmp/arkwood_wl_merged.json
python3 scripts/compute_scores.py /tmp/arkwood_wl_merged.json > /tmp/arkwood_wl_scores.json
```

Note: Watchlist fetch skips ARK and news scripts to keep it fast. If a watchlist fetch fails, note and continue — do not abort.

---

## Step 3: Check Alerts

For each ticker in portfolio.csv, run all checks below. Accumulate all triggered alerts into a single ALERTS list. Each entry has: `alert_category`, `ticker`, `message`, `emoji`, `confidence`, `recommended_action`.

### 3a. Price Alerts (existing)

Compare `current_price` from market data to `alert_below` and `alert_above` columns:
- `PRICE BELOW ALERT: {TICKER} @ ${current_price} — below alert level ${alert_below} ({pct}% below)`
- `PRICE ABOVE ALERT: {TICKER} @ ${current_price} — above alert level ${alert_above} ({pct}% above)`

### 3b. Thesis Drift Alert (existing)

Find the most recent prior snapshot in `data/snapshots/` (pattern: `YYYYMMDD_portfolio_scores.json` first, then `YYYYMMDD_portfolio_snapshot.json`). If `auto_total` in today's scores drops more than 10 points vs prior:
- `SCORE ALERT: {TICKER} TVS auto_total dropped from {prior} to {current}`

If no prior snapshot exists for a ticker: note "First run — no prior snapshot for comparison."

### 3c. V2 Strategy Alerts

Read `v2_signal` from `/tmp/arkwood_daily_scores.json` for each ticker. Also read the top-level `macro_state` field.
If `v2_signal` is null or `v2_action` is `DATA_MISSING`, skip 3c for that ticker and note missing data.

**V2 alert matrix — map `v2_action` to alert category and emoji:**

| v2_action | Category | Emoji | Priority |
|-----------|----------|-------|----------|
| `SELL` | SELL | 🔴 | 1 (highest) |
| `WATCH_EXIT` | WATCH_EXIT | 🔴 | 2 |
| `RISK_OFF_HOLD` | MACRO_RISK | 🟠 | 3 |
| `HOLD_EXTENDED` | EXTENDED | 🟡 | 4 |
| `WAIT` | WAIT | 🟡 | 5 |
| `ADD` | OPPORTUNITY | 🟢 | 6 |
| `HOLD` | — | omit from alerts | — |

For each alert, include in the message:
- `stock_class` (COMPOUNDER / CYCLICAL / HIGH_VOL / EMERGING)
- `overlay_rating`
- `v2_rationale` (already explains the rule that fired)
- `consecutive_avoid` if true (COMPOUNDER patience rule context)
- `persistence_confirmed` if relevant (HIGH_VOL 2-week confirmation)

**Confidence assignment:**
- HIGH: `v2_action == SELL` with consecutive_avoid, OR `v2_action == ADD` with overlay STRONG_SETUP
- MEDIUM: `v2_action == SELL` (single AVOID for non-COMPOUNDER), OR `v2_action == ADD` with overlay SETUP
- LOW: `v2_action == WATCH_EXIT`, WAIT, or any DATA_MISSING case

**Also add a macro banner at the top of the Technical Alerts section:**
- If `macro_state == RISK_ON`: "🟢 MACRO: RISK_ON — SPY above SMA200. All entry signals active."
- If `macro_state == RISK_OFF`: "🔴 MACRO: RISK_OFF — SPY below SMA200. No new entries. Exits accelerated."
- If `macro_state == UNKNOWN`: "⚠️ MACRO: UNKNOWN — SPY SMA200 data unavailable."

### 3d. Watchlist Entry Opportunity Alerts (new)

Read `/tmp/arkwood_wl_scores.json` and cross-reference with `watchlist.csv` (`target_entry`, `priority`).

For each watchlist ticker, evaluate:

| Verdict | Conditions | Emoji |
|---------|-----------|-------|
| ENTRY_OPPORTUNITY | auto_total ≥ 20 AND overlay SETUP or STRONG_SETUP AND price ≤ target_entry × 1.05 (within 5%) | 🟢 |
| APPROACHING | auto_total ≥ 20 AND overlay SETUP or STRONG_SETUP AND price within 15% above target_entry | 🟡 |
| WATCH | auto_total ≥ 20 AND overlay NEUTRAL or EXTENDED | 🟡 |
| AVOID | overlay == AVOID (bearish_count ≥ 2) | 🔴 |
| NOT_YET | all other cases | — (omit from alerts, include only in Watchlist Pulse section) |

Only add ENTRY_OPPORTUNITY, APPROACHING, and AVOID verdicts to the main ALERTS list (to appear in Telegram). WATCH and NOT_YET are shown in the Watchlist Pulse section only.

---

## Step 4: Write the Report

Report file: `reports/{YYYYMMDD}_daily_monitor.md`

```
# ARKWOOD Daily Portfolio Briefing — {DATE}
Generated: {TIME UTC}
Data quality: [note any PARTIAL/EMPTY sources]

---

## Portfolio Alerts

### Technical Alerts
{RISK / EXTENDED_TRIM / CONFIRMED_SELL / WAIT / OPPORTUNITY / SETUP_FORMING alerts from Step 3c}

### Price Alerts
{PRICE BELOW/ABOVE ALERT entries from Step 3a}

### Score Alerts
{SCORE ALERT entries from Step 3b}

{If none in any category: "No alerts today."}

---

## Portfolio Summary Table

| Ticker | Class | Shares | Avg Cost | Current Price | Current Value | P&L ($) | P&L (%) | TVS Auto | Overlay | V2 Action |
|--------|-------|--------|----------|--------------|--------------|---------|---------|----------|---------|-----------|

**Total Portfolio Value:** ${sum of current values}
**Total P&L:** ${total pnl} ({total pnl %})

---

## Portfolio Health Score

Weighted average TVS auto_total across portfolio (weighted by current_value / total_portfolio_value):
**Portfolio Health: {weighted avg TVS auto_total} / 45 (auto-scored components)**

Distribution by portfolio weight:
- STRONG BUY positions: X% of portfolio
- BUY positions: X% of portfolio
- HOLD positions: X% of portfolio
- SELL positions: X% of portfolio

---

## Per-Position Notes

For each holding, write 2–4 sentences covering:
1. What changed overnight (price move, news)
2. Score delta vs prior snapshot (if available)
3. Technical overlay: current rating and what it means for timing
4. Recommended action if anything has changed: BUY MORE / HOLD / TRIM / WATCH / SELL

Flag stale data explicitly if a field is missing.

---

## Watchlist Pulse

For each ticker in watchlist.csv, show a structured entry signal line:

```
{EMOJI} {TICKER} — ${current_price} | TVS: {auto_total} | Overlay: {overlay_rating} | vs Target: {pct_vs_target}% {above/below} ${target_entry} | {VERDICT} — {one sentence}
```

Verdict and emoji:
- 🟢 **ENTRY_OPPORTUNITY** — price at/below target, quality setup, buy signal active
- 🟡 **APPROACHING** — quality setup but price still above target; monitor for dip
- 🟡 **WATCH** — fundamentals OK but technically NEUTRAL or EXTENDED; no entry yet
- 🔴 **AVOID** — technical structure broken (overlay AVOID); wait for recovery
- ⚪ **NOT YET** — price too far above target, or TVS too low

If market or technicals data unavailable for a ticker: note "Data unavailable — cannot score."
```

---

## Step 5: Send Telegram Notification

Build an alerts-only message from the ALERTS list compiled in Step 3.

Sort by priority: 🔴 first, then 🟡, then 🟢, then 🔵.

Format:
```
ARKWOOD Daily Alerts — {YYYY-MM-DD}

🔴 {CATEGORY}: {TICKER} — {one-line message}
🟡 {CATEGORY}: {TICKER} — {one-line message}
🟢 {CATEGORY}: {TICKER} — {one-line message}
🔵 {CATEGORY}: {TICKER} — {one-line message}

{N} alerts · Full report: reports/{YYYYMMDD}_daily_monitor.md
```

If no alerts triggered:
```
ARKWOOD Daily Alerts — {YYYY-MM-DD}

All clear. No alerts today.
Full report: reports/{YYYYMMDD}_daily_monitor.md
```

Send via:
```bash
python3 scripts/notify_telegram.py --message "{formatted_message}"
```

---

## Step 6: Archive Snapshot

```bash
cp /tmp/arkwood_daily_merged.json data/snapshots/{YYYYMMDD}_portfolio_snapshot.json
cp /tmp/arkwood_daily_scores.json data/snapshots/{YYYYMMDD}_portfolio_scores.json
```

Do NOT commit reports/ or snapshots/ to git.
