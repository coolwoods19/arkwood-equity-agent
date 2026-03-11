"""
main.py — ARKWOOD FIU Dashboard API
FastAPI app with all routes inline (v1 — no router split).
Serves portfolio data from existing CSV/JSON snapshot files.
portfolio.csv is READ-ONLY. reports/ is never exposed.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from services.csv_reader import read_portfolio, read_watchlist, all_tickers
from services.snapshot_reader import (
    build_portfolio_response,
    build_ticker_detail,
    get_latest_snapshot_date,
)
from services.thesis_reader import read_thesis
from services.refresh_runner import run_refresh

app = FastAPI(title="ARKWOOD FIU API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    from pathlib import Path
    data_dir = Path(__file__).parent.parent / "data"
    return {
        "status": "ok",
        "latest_snapshot": get_latest_snapshot_date(),
        "data_dir": str(data_dir.resolve()),
    }


# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------

@app.get("/api/portfolio")
def portfolio():
    holdings_csv = read_portfolio()
    return build_portfolio_response(holdings_csv)


# ---------------------------------------------------------------------------
# Ticker detail
# ---------------------------------------------------------------------------

@app.get("/api/ticker/{symbol}")
def ticker_detail(symbol: str):
    symbol = symbol.upper()
    holdings_csv = read_portfolio()
    watchlist_csv = read_watchlist()

    holding = next((h for h in holdings_csv if h["ticker"] == symbol), None)
    watchlist_item = next((w for w in watchlist_csv if w["ticker"] == symbol), None)

    if holding is None and watchlist_item is None:
        raise HTTPException(status_code=404, detail=f"Ticker {symbol} not found in portfolio or watchlist")

    detail = build_ticker_detail(symbol, holding, watchlist_item)

    # Attach watchlist metadata if applicable
    if watchlist_item:
        detail["watchlist"] = {
            "why_watching": watchlist_item.get("why_watching"),
            "target_entry": watchlist_item.get("target_entry"),
            "priority": watchlist_item.get("priority"),
            "date_added": watchlist_item.get("date_added"),
        }
    else:
        detail["watchlist"] = None

    return detail


# ---------------------------------------------------------------------------
# Watchlist
# ---------------------------------------------------------------------------

@app.get("/api/watchlist")
def watchlist():
    from services.snapshot_reader import get_latest_portfolio_snapshot, get_latest_portfolio_scores, derive_rating

    snapshot = get_latest_portfolio_snapshot() or {}
    scores_data = get_latest_portfolio_scores() or {}
    snap_tickers = snapshot.get("tickers", {})
    scores_map = scores_data.get("scores", {})

    items = []
    for w in read_watchlist():
        ticker = w["ticker"]
        snap = snap_tickers.get(ticker, {})
        score = scores_map.get(ticker, {})

        market = snap.get("market", {}) or {}
        overlay = (score.get("technical_overlay") or {})
        overlay_rating = overlay.get("overlay_rating")
        auto_total = score.get("auto_total")
        has_snapshot = bool(snap and not snap.get("market", {}).get("_missing"))

        items.append({
            "ticker": ticker,
            "sector": w.get("sector"),
            "why_watching": w.get("why_watching"),
            "target_entry": w.get("target_entry"),
            "priority": w.get("priority"),
            "date_added": w.get("date_added"),
            "current_price": market.get("current_price") if has_snapshot else None,
            "overlay_rating": overlay_rating,
            "has_snapshot": has_snapshot,
            "rating": derive_rating(auto_total, overlay_rating) if auto_total is not None else None,
        })

    return {"items": items}


# ---------------------------------------------------------------------------
# Refresh (SSE)
# ---------------------------------------------------------------------------

@app.get("/api/refresh/stream")
async def refresh_stream():
    tickers = all_tickers()

    async def event_generator():
        async for chunk in run_refresh(tickers):
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
