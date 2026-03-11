"""
thesis_reader.py — ARKWOOD FIU
Reads per-ticker thesis markdown files from data/thesis/.
"""

from pathlib import Path
from typing import Optional

THESIS_DIR = Path(__file__).parent.parent.parent / "data" / "thesis"


def read_thesis(ticker: str) -> Optional[str]:
    """Returns raw markdown string for ticker, or None if file doesn't exist."""
    path = THESIS_DIR / f"{ticker.upper()}.md"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def thesis_exists(ticker: str) -> bool:
    return (THESIS_DIR / f"{ticker.upper()}.md").exists()
