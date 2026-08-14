"""Fetch screener.in company pages for the tracked universe, politely.

Throttled + jittered sequential fetches (screener.in is a small free service —
be a good citizen, never hammer). Each stock is resilient: one failed fetch is
logged + skipped, never fatal. Returns parsed fundamentals per ticker.
"""

from __future__ import annotations

import logging
import random
import time

from .. import config as C
from ..util import fetch_text
from .parser import parse_company

log = logging.getLogger("screen_watch")


def fetch_one(ticker: str) -> dict | None:
    """Fetch + parse one company page. None on network/HTTP failure."""
    try:
        html = fetch_text(C.company_url(ticker))
    except Exception as e:  # noqa: BLE001 — resilient: skip bad stock
        log.warning("fetch failed %s: %s", ticker, e)
        return None
    return parse_company(html, ticker)


def fetch_fundamentals(tickers: list[str]) -> list[dict]:
    """Sequentially fetch every ticker with throttle+jitter between requests.
    Skips failures. Returns parsed rows in universe order."""
    rows: list[dict] = []
    for i, t in enumerate(tickers):
        if i:
            time.sleep(C.THROTTLE_SECONDS + random.uniform(0, C.JITTER_SECONDS))
        row = fetch_one(t)
        if row is not None:
            rows.append(row)
    log.info("fetched %d/%d company pages", len(rows), len(tickers))
    return rows
