"""Telegram notifier (HTML). Best-effort, reads config from env, no-ops when
unconfigured (TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID — the single oriz bot,
NEVER hardcoded). Fires when a stock newly enters the top-N value rank.
"""

from __future__ import annotations

import logging
import os

import httpx

from .. import config as C

log = logging.getLogger("screen_watch")


def _esc(s: object) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _stock_line(s: dict) -> str:
    ticker = _esc(s["ticker"])
    url = f"{C.SCREENER_BASE}/company/{s['ticker']}/"
    bits = [f"#{s.get('rank')} <a href=\"{url}\"><b>{ticker}</b></a>"]
    if s.get("current_price") is not None:
        bits.append(f"₹{s['current_price']:g}")
    if s.get("pe") is not None:
        bits.append(f"PE {s['pe']:g}")
    if s.get("pb") is not None:
        bits.append(f"PB {s['pb']:g}")
    if s.get("dividend_yield") is not None:
        bits.append(f"DY {s['dividend_yield']:g}%")
    bits.append(f"val {s.get('value_score')}")
    return " · ".join(bits)


def format_message(new_rows: list[dict], top_n: int) -> str:
    plural = "" if len(new_rows) == 1 else "S"
    head = (f'💎 <a href="{C.SITE}"><b>{len(new_rows)} NEWLY-CHEAP STOCK{plural} '
            f'— entered top {top_n} value rank</b></a>')
    lines = [head]
    for s in sorted(new_rows, key=lambda x: x.get("rank", 1e9)):
        lines.append(_stock_line(s))
    lines.append(f"→ {C.SITE}")
    return "\n".join(lines)


def send_telegram(message: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        log.info("telegram: TELEGRAM_BOT_TOKEN/CHAT_ID unset — skipping")
        return False
    try:
        r = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "HTML",
                  "disable_web_page_preview": True},
            timeout=20,
        )
        r.raise_for_status()
        log.info("telegram: sent")
        return True
    except Exception as e:  # noqa: BLE001
        log.warning("telegram send failed: %s", e)
        return False


def notify_new_top(new_rows: list[dict], top_n: int) -> bool:
    """Send one combined message for the newly-cheap stocks. No-op if empty."""
    if not new_rows:
        log.info("notify: no new top-%d entrants", top_n)
        return False
    return send_telegram(format_message(new_rows, top_n))
