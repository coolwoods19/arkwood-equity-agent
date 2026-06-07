# ARKWOOD Financial Intelligence Unit (FIU)

A stock research and portfolio monitoring system combining ARK Invest–style disruptive innovation analysis with automated data pipelines and a React dashboard.

## Overview

ARKWOOD FIU fetches live market data, fundamentals, ARK holdings, news sentiment, and technical signals for any ticker. It computes a deterministic auto score (0-45), prepares the remaining analyst-scored TVS criteria, and surfaces dashboard ratings from the auto score plus the technical overlay.

## Features

- **TVS Scoring** — deterministic auto scoring plus pending analyst-scored criteria
- **Technical Overlay** — trend, momentum, breakout, and relative strength signals (separate from TVS)
- **Daily Portfolio Monitor** — morning sweep with alerts, scoring, and Telegram notifications
- **Deep Stock Analysis** — full 11-section ARKWOOD institutional research report
- **Thesis Tracking** — per-ticker investment thesis files with confidence ratings
- **Watchlist Screening** — idea scan to surface high-fit ARKWOOD candidates
- **React Dashboard** — live frontend with portfolio overview, watchlist, and analysis tabs

## Tech Stack

- **Backend:** Python 3, FastAPI
- **Frontend:** React + TypeScript + Vite
- **Data:** yfinance, Yahoo Finance news, ARK Invest CSVs
- **Notifications:** Telegram Bot API
- **AI Orchestration:** Claude Code (claude.ai/code) with custom skills

## Directory Structure

```
arkwood-equity-agent/
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
│   └── notify_telegram.py
├── data/
│   ├── portfolio.example.csv
│   ├── watchlist.example.csv
│   ├── portfolio.csv       # Local only; ignored by git
│   ├── watchlist.csv       # Local only; ignored by git
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

## Scoring System

The app separates mechanical scoring from analyst judgment:

| Score | Max Points | Status |
|---|---|
| Auto score | 45 | Computed by `scripts/compute_scores.py` |
| Manual/analyst criteria | 80 | Prepared as placeholders for Claude or analyst review |
| Full TVS | 125 | Available only after manual criteria are filled |

Dashboard ratings currently use the auto score plus the technical overlay. Technical overlay (trend/momentum/breakout/relative strength) is computed separately and does not affect the TVS score.

## Setup

### Environment variables (optional)

```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

Copy the example env file if you want Telegram notifications:

```bash
cp .env.example .env
```

### Local data files

Real portfolio and watchlist files are local-only and ignored by git:

```bash
cp data/portfolio.example.csv data/portfolio.csv
cp data/watchlist.example.csv data/watchlist.csv
```

Edit those local CSVs with your own holdings and watchlist. Do not commit real positions, cost basis, generated snapshots, reports, or local Claude settings to a public repo.

### Install dependencies

```bash
pip3 install -r requirements.txt
```

### Smoke test

```bash
python3 scripts/fetch_market_data.py NVDA > /tmp/arkwood_market.json
python3 scripts/fetch_fundamentals.py NVDA > /tmp/arkwood_fundamentals.json
python3 scripts/fetch_ark_holdings.py NVDA > /tmp/arkwood_ark.json
python3 scripts/fetch_news.py NVDA > /tmp/arkwood_news.json
python3 scripts/fetch_technicals.py NVDA > /tmp/arkwood_technicals.json
python3 scripts/merge_data.py /tmp/arkwood_market.json /tmp/arkwood_fundamentals.json /tmp/arkwood_ark.json /tmp/arkwood_news.json /tmp/arkwood_technicals.json > /tmp/arkwood_merged.json
python3 scripts/compute_scores.py /tmp/arkwood_merged.json
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
