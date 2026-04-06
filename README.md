# ARKWOOD Financial Intelligence Unit (FIU)

An institutional-grade stock research and portfolio monitoring system combining ARK Invest–style disruptive innovation analysis with automated data pipelines and a React dashboard.

## Overview

ARKWOOD FIU fetches live market data, fundamentals, ARK holdings, news sentiment, and technical signals for any ticker — then scores it using the **TVS (Technology Value Score)** framework (0–125) to surface the highest-conviction disruptive innovation plays.

## Features

- **TVS Scoring** — quantitative + qualitative scoring across growth, valuation, and ARK conviction dimensions
- **Technical Overlay** — trend, momentum, breakout, and relative strength signals (separate from TVS)
- **Daily Portfolio Monitor** — morning sweep with alerts, scoring, and Telegram notifications
- **Deep Stock Analysis** — full 11-section ARKWOOD institutional research report
- **Thesis Tracking** — per-ticker investment thesis files with confidence ratings
- **Watchlist Screening** — idea scan to surface high-fit ARKWOOD candidates
- **Backtest Evaluation** — strategy backtesting and grading pipeline
- **React Dashboard** — live frontend with portfolio overview, watchlist, and analysis tabs

## Tech Stack

- **Backend:** Python 3, FastAPI
- **Frontend:** React + TypeScript + Vite
- **Data:** yfinance, NewsAPI, ARK Invest CSVs
- **Notifications:** Telegram Bot API
- **AI Orchestration:** Claude Code (claude.ai/code) with custom skills

## Directory Structure

```
stock-agent/
├── api/                    # FastAPI backend
│   ├── main.py
│   └── services/
├── frontend/               # React + TypeScript dashboard
│   └── src/
│       ├── components/     # OverviewTab, Sidebar, etc.
│       └── types.ts
├── scripts/                # Data fetch & scoring pipeline
│   ├── fetch_market_data.py
│   ├── fetch_fundamentals.py
│   ├── fetch_ark_holdings.py
│   ├── fetch_news.py
│   ├── fetch_technicals.py
│   ├── merge_data.py
│   ├── compute_scores.py
│   ├── compute_dynamic_alerts.py
│   ├── run_backtest.py
│   └── notify_telegram.py
├── data/
│   ├── portfolio.csv       # Holdings: ticker, shares, avg_cost, alerts, sector
│   ├── watchlist.csv       # Candidates under consideration
│   ├── thesis/             # Per-ticker investment thesis markdown files
│   └── snapshots/          # Daily JSON snapshots (gitignored)
├── reports/                # Generated reports (gitignored, local only)
└── .claude/skills/         # Claude Code slash command skill prompts
```

## Data Pipeline

```
fetch_market_data.py   ─┐
fetch_fundamentals.py  ─┤
fetch_ark_holdings.py  ─┼─► merge_data.py ─► compute_scores.py ─► Claude qualitative scoring
fetch_news.py          ─┤
fetch_technicals.py    ─┘
                                              └─► notify_telegram.py
```

### Running scripts individually

```bash
python3 scripts/fetch_market_data.py TSLA NVDA
python3 scripts/fetch_fundamentals.py TSLA
python3 scripts/fetch_ark_holdings.py TSLA
python3 scripts/fetch_news.py TSLA
python3 scripts/fetch_technicals.py TSLA

python3 scripts/merge_data.py market.json fund.json ark.json news.json tech.json > merged.json
python3 scripts/compute_scores.py merged.json
```

## TVS Scoring System (0–125)

| Section | Max Points |
|---|---|
| A. Growth & Innovation (revenue growth, moat, S-curve, margins, Wright's Law, convergence, disruption driver) | 70 |
| B. Valuation & Fundamentals (forward PEG, cash runway, upside to target, relative multiples) | ±20 to +40 |
| C. Momentum & ARK Conviction (ARK weight, recent catalyst) | 15 |

Technical overlay (trend/momentum/breakout/relative strength) is computed separately and does not affect the TVS score.

## Setup

### Environment variables (optional)

```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Install dependencies

```bash
pip3 install -r api/requirements.txt
```

### Run the API

```bash
uvicorn api.main:app --reload
```

### Run the frontend

```bash
cd frontend
npm install
npm run dev
```

## Investment Philosophy

- Disruptive innovation platforms riding S-curves and Wright's Law cost declines
- Companies that **drive** disruption (platform/core enabler) over those that merely leverage it
- Convergence of multiple platforms (AI + Robotics, Genomics + Precision Medicine, Blockchain + Fintech)
- Founder-led or technically expert leadership
- Sectors: AI · Robotics · Energy Storage · Genomics/MedTech · Blockchain/Fintech · EV · Space · 3D Printing

## Covered Horizons

- **1-year tactical** — near-term price targets, catalysts, risk events
- **3–5 year strategic** — innovation thesis, TAM expansion, structural positioning
