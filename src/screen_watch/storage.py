"""git-as-DB persistence — all state lives in data/*.json, committed each run.

  data/stocks.json          latest scored universe + meta (site contract)
  data/history/<date>.json  daily append-only snapshot (audit + charts)
  data/notify-state.json    {topIds:[...], notifiedAt} — drives change-only alerts

Pure helpers (detect_new_top) are backend-free + unit-tested directly.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from . import config as C

log = logging.getLogger("screen_watch")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def data_dir() -> Path:
    d = C._repo_root() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _load(name: str, default):
    f = data_dir() / name
    if not f.exists():
        return default
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        log.warning("could not read %s: %s", name, e)
        return default


def _write(name: str, payload) -> None:
    f = data_dir() / name
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_stocks(scored: list[dict]) -> str:
    """stocks.json = latest ranked universe (+ ts). Also append a daily history
    snapshot. Returns the run timestamp."""
    ts = _now_iso()
    _write("stocks.json", {"ts": ts, "count": len(scored), "stocks": scored})
    day = ts[:10]
    _write(f"history/{day}.json", {"ts": ts, "stocks": scored})
    log.info("wrote stocks.json + history/%s.json (%d stocks)", day, len(scored))
    return ts


def load_notify_state() -> dict:
    return _load("notify-state.json", {"topIds": [], "notifiedAt": None})


def save_notify_state(top_ids: list[str], notified_at: str | None = None) -> None:
    at = notified_at or _now_iso()
    _write("notify-state.json", {"topIds": sorted(top_ids), "notifiedAt": at, "updatedAt": at})


def detect_new_top(scored: list[dict], prev_top_ids, top_n: int) -> tuple[list[dict], set[str]]:
    """Stocks whose rank is now within top-N and were NOT in the previous top set
    ("newly cheap"). Returns (new-entrant rows, current top-N id set)."""
    prev = prev_top_ids if isinstance(prev_top_ids, set) else {str(x) for x in (prev_top_ids or [])}
    current_top = [s for s in scored if s.get("rank") and s["rank"] <= top_n]
    current_ids = {s["ticker"] for s in current_top}
    new_rows = [s for s in current_top if s["ticker"] not in prev]
    return new_rows, current_ids
