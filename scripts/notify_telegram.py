"""
notify_telegram.py — ARKWOOD FIU
Sends portfolio briefing summaries to a Telegram bot.

Usage:
    python3 scripts/notify_telegram.py --report reports/20260309_daily_monitor.md
    python3 scripts/notify_telegram.py --message "Alert: TSLA crossed above $320"

Environment variables required:
    TELEGRAM_BOT_TOKEN   — from BotFather
    TELEGRAM_CHAT_ID     — your personal or group chat ID

If env vars are missing, the script exits cleanly (non-fatal) so it doesn't
block the daily monitor orchestration.
"""

import sys
import os
import argparse
import re
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    print("notify_telegram.py: requests not installed. Run: pip3 install requests")
    sys.exit(0)  # non-fatal exit

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MESSAGE_CHARS = 4096


def get_env() -> tuple[str, str]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    return token, chat_id


def extract_summary_from_report(path: str) -> str:
    """
    Extract a concise summary from the daily monitor markdown report.
    Pulls: Portfolio Alerts section + Portfolio Summary Table + Total P&L line.
    """
    try:
        with open(path) as f:
            content = f.read()
    except FileNotFoundError:
        return f"[Error: report file not found at {path}]"

    lines = content.splitlines()
    summary_parts = []

    # Extract report header (first 3 lines)
    summary_parts.append("\n".join(lines[:3]))
    summary_parts.append("")

    # Extract Portfolio Alerts section
    alerts_match = re.search(
        r"## Portfolio Alerts\n(.*?)(?=\n---|\n## )", content, re.DOTALL
    )
    if alerts_match:
        summary_parts.append("*Portfolio Alerts*")
        summary_parts.append(alerts_match.group(1).strip())
        summary_parts.append("")

    # Extract Portfolio Summary Table (table rows only, max 20 lines)
    table_match = re.search(
        r"## Portfolio Summary Table\n(.*?)(?=\n---|\n## )", content, re.DOTALL
    )
    if table_match:
        table_text = table_match.group(1).strip()
        table_lines = table_text.splitlines()[:22]  # header + up to 20 rows
        summary_parts.append("*Portfolio Summary*")
        summary_parts.append("```")
        summary_parts.append("\n".join(table_lines))
        summary_parts.append("```")
        summary_parts.append("")

    # Extract Total P&L line
    pnl_match = re.search(r"\*\*Total P&L.*?\*\*.*", content)
    if pnl_match:
        summary_parts.append(pnl_match.group(0))
        summary_parts.append("")

    # Extract Portfolio Health Score (first 3 lines of that section)
    health_match = re.search(
        r"## Portfolio Health Score\n(.*?)(?=\n---|\n## )", content, re.DOTALL
    )
    if health_match:
        health_lines = health_match.group(1).strip().splitlines()[:4]
        summary_parts.append("*Portfolio Health*")
        summary_parts.append("\n".join(health_lines))

    result = "\n".join(summary_parts)

    # Truncate to Telegram limit, preserving whole lines
    if len(result) > MAX_MESSAGE_CHARS:
        result = result[:MAX_MESSAGE_CHARS - 50]
        result = result.rsplit("\n", 1)[0]  # cut at last newline
        result += "\n\n[Report truncated — see full file in reports/]"

    return result


def send_message(token: str, chat_id: str, text: str) -> bool:
    url = TELEGRAM_API.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            print("Telegram notification sent.")
            return True
        else:
            print(f"Telegram send failed: HTTP {resp.status_code} — {resp.text}", file=sys.stderr)
            return False
    except requests.RequestException as e:
        print(f"Telegram send failed: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="ARKWOOD Telegram notifier")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--report", help="Path to a markdown report file to summarize and send")
    group.add_argument("--message", help="Send a custom text message directly")
    args = parser.parse_args()

    token, chat_id = get_env()

    if not token or not chat_id:
        print(
            "notify_telegram.py: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — skipping notification.\n"
            "Set them with:\n"
            "  export TELEGRAM_BOT_TOKEN='your_token'\n"
            "  export TELEGRAM_CHAT_ID='your_chat_id'"
        )
        sys.exit(0)  # non-fatal

    if args.report:
        text = extract_summary_from_report(args.report)
    else:
        text = args.message

    if not text:
        print("notify_telegram.py: Empty message — nothing to send.")
        sys.exit(0)

    success = send_message(token, chat_id, text)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
