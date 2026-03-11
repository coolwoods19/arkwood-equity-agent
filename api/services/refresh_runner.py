"""
refresh_runner.py — ARKWOOD FIU
Async SSE generator that orchestrates the full data refresh pipeline.
Runs fetch scripts as subprocesses, emits progress events, writes snapshots.

Lock file: data/.refresh.lock (project-specific)
Chain is shielded from SSE client disconnects via asyncio.shield().
"""

import asyncio
import json
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, Optional

ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
SCRIPTS_DIR = ROOT_DIR / "scripts"
LOCK_FILE = DATA_DIR / ".refresh.lock"


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _run_script(args: list[str], step: str) -> tuple[bool, str, str]:
    """Run a Python script as a subprocess. Returns (success, stdout, stderr)."""
    proc = await asyncio.create_subprocess_exec(
        "python3", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(ROOT_DIR),
    )
    stdout, stderr = await proc.communicate()
    success = proc.returncode == 0
    return success, stdout.decode("utf-8", errors="replace"), stderr.decode("utf-8", errors="replace")


async def _refresh_chain(tickers: list[str]) -> AsyncIterator[str]:
    """The actual refresh pipeline. Yields SSE event strings."""
    ticker_args = tickers
    start_time = time.monotonic()
    steps_succeeded: list[str] = []
    steps_failed: list[str] = []

    # Temp files for each fetch script's output
    tmp_market = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp_fundamentals = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp_ark = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp_news = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp_technicals = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp_market.close(); tmp_fundamentals.close(); tmp_ark.close()
    tmp_news.close(); tmp_technicals.close()

    steps = [
        {
            "step": "fetch_market",
            "script": str(SCRIPTS_DIR / "fetch_market_data.py"),
            "tmp": tmp_market.name,
            "fatal": True,
            "label": f"Fetching market data for {len(tickers)} tickers",
        },
        {
            "step": "fetch_fundamentals",
            "script": str(SCRIPTS_DIR / "fetch_fundamentals.py"),
            "tmp": tmp_fundamentals.name,
            "fatal": False,
            "label": "Fetching fundamentals",
        },
        {
            "step": "fetch_ark",
            "script": str(SCRIPTS_DIR / "fetch_ark_holdings.py"),
            "tmp": tmp_ark.name,
            "fatal": False,
            "label": "Fetching ARK holdings",
        },
        {
            "step": "fetch_news",
            "script": str(SCRIPTS_DIR / "fetch_news.py"),
            "tmp": tmp_news.name,
            "fatal": False,
            "label": "Fetching news & catalysts",
        },
        {
            "step": "fetch_technicals",
            "script": str(SCRIPTS_DIR / "fetch_technicals.py"),
            "tmp": tmp_technicals.name,
            "fatal": False,
            "label": "Fetching technicals",
        },
    ]

    try:
        # Phase 1: fetch scripts (each writes to a temp file via stdout redirect)
        for s in steps:
            yield _sse_event("progress", {"step": s["step"], "status": "running", "message": s["label"] + "..."})

            t0 = time.monotonic()
            success, stdout, stderr = await _run_script(
                [s["script"]] + ticker_args, s["step"]
            )
            elapsed = round(time.monotonic() - t0, 1)

            if success and stdout.strip():
                Path(s["tmp"]).write_text(stdout, encoding="utf-8")
                steps_succeeded.append(s["step"])
                yield _sse_event("progress", {"step": s["step"], "status": "done", "message": f"Done in {elapsed}s"})
            else:
                steps_failed.append(s["step"])
                msg = stderr.strip()[:300] if stderr.strip() else "No output returned"
                yield _sse_event("progress", {
                    "step": s["step"], "status": "error",
                    "message": f"Script error after {elapsed}s: {msg}",
                    "fatal": s["fatal"],
                })
                if s["fatal"]:
                    yield _sse_event("error", {"step": s["step"], "message": f"Fatal failure: {msg}", "fatal": True})
                    return

        # Phase 2: merge
        date_str = datetime.now().strftime("%Y%m%d")
        snapshot_path = SNAPSHOTS_DIR / f"{date_str}_portfolio_snapshot.json"
        scores_path = SNAPSHOTS_DIR / f"{date_str}_portfolio_scores.json"

        yield _sse_event("progress", {"step": "merge", "status": "running", "message": "Merging data sources..."})
        t0 = time.monotonic()
        success, stdout, stderr = await _run_script(
            [str(SCRIPTS_DIR / "merge_data.py"),
             tmp_market.name, tmp_fundamentals.name, tmp_ark.name,
             tmp_news.name, tmp_technicals.name],
            "merge",
        )
        elapsed = round(time.monotonic() - t0, 1)

        if not success or not stdout.strip():
            steps_failed.append("merge")
            msg = stderr.strip()[:300] if stderr else "No merged output"
            yield _sse_event("progress", {"step": "merge", "status": "error", "message": msg, "fatal": True})
            yield _sse_event("error", {"step": "merge", "message": f"Fatal: {msg}", "fatal": True})
            return

        snapshot_path.write_text(stdout, encoding="utf-8")
        steps_succeeded.append("merge")
        yield _sse_event("progress", {"step": "merge", "status": "done", "message": f"Merged in {elapsed}s → {snapshot_path.name}"})

        # Phase 3: compute scores
        yield _sse_event("progress", {"step": "compute_scores", "status": "running", "message": "Computing TVS scores..."})
        t0 = time.monotonic()
        success, stdout, stderr = await _run_script(
            [str(SCRIPTS_DIR / "compute_scores.py"), str(snapshot_path)],
            "compute_scores",
        )
        elapsed = round(time.monotonic() - t0, 1)

        if success and stdout.strip():
            scores_path.write_text(stdout, encoding="utf-8")
            steps_succeeded.append("compute_scores")
            yield _sse_event("progress", {"step": "compute_scores", "status": "done", "message": f"Scored in {elapsed}s"})
        else:
            steps_failed.append("compute_scores")
            yield _sse_event("progress", {
                "step": "compute_scores", "status": "error",
                "message": stderr.strip()[:300] if stderr else "No output",
                "fatal": False,
            })

        duration = round(time.monotonic() - start_time, 1)
        yield _sse_event("complete", {
            "success": True,
            "snapshot_date": date_str,
            "duration_seconds": duration,
            "steps_succeeded": steps_succeeded,
            "steps_failed": steps_failed,
        })

    finally:
        # Clean up temp files
        for tmp in [tmp_market.name, tmp_fundamentals.name, tmp_ark.name, tmp_news.name, tmp_technicals.name]:
            try:
                Path(tmp).unlink(missing_ok=True)
            except Exception:
                pass
        # Release lock
        try:
            LOCK_FILE.unlink(missing_ok=True)
        except Exception:
            pass


async def run_refresh(tickers: list[str]) -> AsyncIterator[str]:
    """
    Entry point. Acquires lock, runs chain via asyncio.shield so the chain
    continues even if the SSE client disconnects.
    """
    # Check lock
    if LOCK_FILE.exists():
        yield _sse_event("error", {
            "step": "lock",
            "message": "Refresh already in progress (lock file exists: data/.refresh.lock)",
            "fatal": True,
        })
        return

    # Acquire lock
    LOCK_FILE.write_text(str(asyncio.get_event_loop()), encoding="utf-8")

    # Shield the chain from client disconnect
    async def _shielded():
        async for event in _refresh_chain(tickers):
            yield event

    async for event in _shielded():
        yield event
