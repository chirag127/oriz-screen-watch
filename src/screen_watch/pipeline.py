"""Pipeline: fetch screener.in fundamentals -> compute value scores + rank ->
write data/*.json (git-as-DB) -> notify on stocks NEWLY entering the top-N.
"""

from __future__ import annotations

import logging

from . import config as C
from . import storage
from .notify.channels import notify_new_top
from .scorer import score
from .sources.screener import fetch_fundamentals

log = logging.getLogger("screen_watch")


def run(with_notify: bool = True, rows: list[dict] | None = None) -> dict:
    """One scrape cycle. `rows` (pre-fetched parsed fundamentals) is for tests;
    None => live fetch. Returns a summary dict."""
    universe = C.tickers()
    if rows is None:
        rows = fetch_fundamentals(universe)
    if not rows:
        log.warning("no fundamentals fetched — nothing to score")
        return {"scored": 0, "notified": False, "new_top": []}

    scored = score(rows)
    storage.write_stocks(scored)

    prev = storage.load_notify_state()
    new_rows, current_ids = storage.detect_new_top(scored, prev.get("topIds"), C.NOTIFY_TOP_N)
    log.info("top-%d: %d stocks (%d newly cheap)", C.NOTIFY_TOP_N, len(current_ids), len(new_rows))

    notified = False
    if with_notify and new_rows:
        notified = notify_new_top(new_rows, C.NOTIFY_TOP_N)
    # always advance state to the current top set (dedup: no re-fire next run)
    storage.save_notify_state(sorted(current_ids))

    return {
        "scored": len(scored),
        "universe": len(universe),
        "top_n": C.NOTIFY_TOP_N,
        "new_top": [s["ticker"] for s in new_rows],
        "notified": notified,
    }
