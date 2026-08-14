"""Rank-change notify logic tests (backend-free pure helper)."""

from screen_watch.storage import detect_new_top


def _scored(order):
    """Build a ranked list from a ticker order (rank = position)."""
    return [{"ticker": t, "rank": i} for i, t in enumerate(order, 1)]


def test_new_entrant_into_top_n_detected():
    scored = _scored(["A", "B", "C", "D"])
    new_rows, current = detect_new_top(scored, prev_top_ids=["A", "B"], top_n=3)
    # top-3 = A,B,C ; prev top = A,B ; newly cheap = C
    assert {r["ticker"] for r in new_rows} == {"C"}
    assert current == {"A", "B", "C"}


def test_no_new_entrant_when_top_unchanged():
    scored = _scored(["A", "B", "C"])
    new_rows, current = detect_new_top(scored, prev_top_ids=["A", "B", "C"], top_n=3)
    assert new_rows == []
    assert current == {"A", "B", "C"}


def test_first_run_all_top_are_new():
    scored = _scored(["A", "B", "C"])
    new_rows, current = detect_new_top(scored, prev_top_ids=[], top_n=2)
    assert {r["ticker"] for r in new_rows} == {"A", "B"}
    assert current == {"A", "B"}


def test_stock_dropping_out_is_not_notified():
    # X was #1, now #5 (out of top-3). Not a "newly cheap" event.
    scored = _scored(["A", "B", "C", "D", "X"])
    new_rows, current = detect_new_top(scored, prev_top_ids=["X", "A", "B"], top_n=3)
    assert {r["ticker"] for r in new_rows} == {"C"}
    assert "X" not in current
