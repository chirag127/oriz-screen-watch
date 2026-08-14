"""Golden parser test — against the REAL screener.in TCS page fixture
(verbatim h1 + #top-ratios captured 2026-08-14). NEVER hits the network."""

from pathlib import Path

from screen_watch.sources.parser import parse_company

FIX = Path(__file__).parent / "fixtures" / "screener_tcs.html"


def _tcs() -> dict:
    return parse_company(FIX.read_text(encoding="utf-8"), "TCS")


def test_parses_core_ratios():
    r = _tcs()
    assert r["ticker"] == "TCS"
    assert "Tata Consultancy Services" in (r["name"] or "")
    assert r["market_cap"] == 851843.0        # ₹ 8,51,843 Cr.
    assert r["current_price"] == 2354.0
    assert r["pe"] == 15.8
    assert r["book_value"] == 234.0
    assert r["dividend_yield"] == 2.70
    assert r["roce"] == 76.7
    assert r["roe"] == 65.2
    assert r["face_value"] == 1.00


def test_parses_high_low():
    r = _tcs()
    assert r["high"] == 3350.0
    assert r["low"] == 1976.0


def test_derives_pb_from_price_over_bookvalue():
    r = _tcs()
    # 2354 / 234 = 10.06
    assert r["pb"] == round(2354.0 / 234.0, 2)


def test_missing_block_returns_nulls_not_fabricated():
    r = parse_company("<html><body><h1>Nothing Ltd</h1></body></html>", "XXXX")
    assert r["name"] == "Nothing Ltd"
    assert r["pe"] is None
    assert r["pb"] is None
    assert r["market_cap"] is None
