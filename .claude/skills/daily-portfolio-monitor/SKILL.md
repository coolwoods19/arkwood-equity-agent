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

```bash
python3 scripts/fetch_market_data.py {TICKER_LIST} > /tmp/arkwood_daily_market.json
python3 scripts/fetch_fundamentals.py {TICKER_LIST} > /tmp/arkwood_daily_fundamentals.json
python3 scripts/fetch_ark_holdings.py {TICKER_LIST} > /tmp/arkwood_daily_ark.json
python3 scripts/fetch_news.py {TICKER_LIST} > /tmp/arkwood_daily_news.json
python3 scripts/merge_data.py \
  /tmp/arkwood_daily_market.json \
  /tmp/arkwood_daily_fundamentals.json \
  /tmp/arkwood_daily_ark.json \
  /tmp/arkwood_daily_news.json > /tmp/arkwood_daily_merged.json
python3 scripts/compute_scores.py /tmp/arkwood_daily_merged.json > /tmp/arkwood_daily_scores.json
```

---

## Step 3: Check Alerts

For each ticker in portfolio.csv, compare `current_price` from market data to `alert_below` and `alert_above` columns.

Build an **ALERTS** list:
- `PRICE BELOW ALERT: {TICKER} @ ${current_price} — below alert level ${alert_below} ({pct}% below)`
- `PRICE ABOVE ALERT: {TICKER} @ ${current_price} — above alert level ${alert_above} ({pct}% above)`

Also check for **thesis drift**: find the most recent prior snapshot in `data/snapshots/` for each ticker (file pattern: `YYYYMMDD_{TICKER}.json` or `YYYYMMDD_portfolio_snapshot.json`). If the auto_total score in today's scores drops more than 10 points vs the prior snapshot, flag: `SCORE ALERT: {TICKER} TVS auto_total dropped from {prior} to {current}`.

If no prior snapshot exists for a ticker, note "First run — no prior snapshot for comparison."

---

## Step 4: Write the Report

Report file: `reports/{YYYYMMDD}_daily_monitor.md`

Use this exact structure:

```
# ARKWOOD Daily Portfolio Briefing — {DATE}
Generated: {TIME UTC}
Data quality: [note any PARTIAL/EMPTY sources]

---

## Portfolio Alerts
{ALERTS list, or "No alerts today."}

---

## Portfolio Summary Table

| Ticker | Shares | Avg Cost | Purchase Value | Current Price | Current Value | P&L ($) | P&L (%) | Rating | TVS Score | Action |
|--------|--------|----------|---------------|--------------|--------------|---------|---------|--------|-----------|--------|

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
3. Recommended action if anything has changed: BUY MORE / HOLD / TRIM / WATCH / SELL

Flag stale data explicitly if a field is missing.

---

## Watchlist Pulse

For each ticker in watchlist.csv: one line update.
Format: `{TICKER} — ${current_price} | {1-sentence note on any significant price move or news}`
If no market data is available, note "Data unavailable."
```

---

## Step 5: Send Telegram Notification

```bash
python3 scripts/notify_telegram.py --report reports/{YYYYMMDD}_daily_monitor.md
```

---

## Step 6: Archive Snapshot

```bash
cp /tmp/arkwood_daily_merged.json data/snapshots/{YYYYMMDD}_portfolio_snapshot.json
```

Do NOT commit reports/ or snapshots/ to git.
