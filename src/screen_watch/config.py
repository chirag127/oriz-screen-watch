"""Central config — the SINGLE source of every screen-watch tunable + constant.
Every module imports from here; nothing hardcoded elsewhere.

TICKERS seed = ~15 liquid PSU/value names (cheap, high-dividend). Overridable:
  - env SCREEN_WATCH_TICKERS = "TCS,ITC,..." (comma/space separated), OR
  - data/watchlist.json = {"tickers": ["TCS", ...]} (git-as-DB, wins over env).

Ticker == NSE symbol == screener.in company slug for NSE-listed names
(https://www.screener.in/company/<TICKER>/).
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def _i(env: str, default: int) -> int:
    try:
        return int(os.environ.get(env, "") or default)
    except ValueError:
        return default


def _f(env: str, default: float) -> float:
    try:
        return float(os.environ.get(env, "") or default)
    except ValueError:
        return default


# ── universe (seed value names — cheap PSU/energy/commodity) ────────────────
DEFAULT_TICKERS: list[str] = [
    "TCS", "ITC", "COALINDIA", "ONGC", "POWERGRID", "NTPC", "BPCL", "HINDPETRO",
    "GAIL", "SAIL", "NMDC", "IOC", "OIL", "RECLTD", "PFC",
]

# ── screener.in ─────────────────────────────────────────────────────────────
SCREENER_BASE = os.environ.get("SCREENER_BASE", "https://www.screener.in").rstrip("/")


def company_url(ticker: str) -> str:
    return f"{SCREENER_BASE}/company/{ticker.strip().upper()}/"


# ── notify gate ─────────────────────────────────────────────────────────────
# Alert when a stock's value-score rank crosses INTO the top-N ("newly cheap").
NOTIFY_TOP_N: int = _i("NOTIFY_TOP_N", 10)

# ── request politeness (never hammer screener.in) ───────────────────────────
REQUEST_TIMEOUT: float = _f("REQUEST_TIMEOUT", 25.0)
THROTTLE_SECONDS: float = _f("THROTTLE_SECONDS", 1.5)   # base delay between fetches
JITTER_SECONDS: float = _f("JITTER_SECONDS", 1.0)       # + random 0..this
MAX_WORKERS: int = _i("MAX_WORKERS", 4)                 # low — be a good citizen

USER_AGENT = os.environ.get(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
)

# ── site ────────────────────────────────────────────────────────────────────
SITE = os.environ.get("SITE_URL", "https://chirag127.github.io/oriz-screen-watch/")


def _repo_root() -> Path:
    # <repo>/src/screen_watch/config.py -> repo root is two up from src
    return Path(__file__).resolve().parent.parent.parent


def tickers() -> list[str]:
    """Resolved universe: data/watchlist.json > env SCREEN_WATCH_TICKERS > default.
    De-duplicated, upper-cased, order preserved."""
    wl = _repo_root() / "data" / "watchlist.json"
    raw: list[str] = []
    if wl.exists():
        try:
            data = json.loads(wl.read_text(encoding="utf-8"))
            raw = list(data.get("tickers", [])) if isinstance(data, dict) else list(data)
        except Exception:  # noqa: BLE001
            raw = []
    if not raw:
        env = os.environ.get("SCREEN_WATCH_TICKERS", "").strip()
        if env:
            raw = [t for t in env.replace(",", " ").split() if t]
    if not raw:
        raw = DEFAULT_TICKERS
    seen: set[str] = set()
    out: list[str] = []
    for t in raw:
        u = t.strip().upper()
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out
