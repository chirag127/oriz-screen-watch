"""Deterministic value-score / z-score math tests with known inputs."""

import math

from screen_watch.scorer import _value_from_avgz, _zscores, score


def test_zscore_population_formula():
    zs = _zscores({"a": 1.0, "b": 2.0, "c": 3.0})
    # population sd of [1,2,3] = sqrt(2/3); mean = 2
    sd = math.sqrt(2 / 3)
    assert zs["a"] == (1 - 2) / sd
    assert zs["b"] == 0.0
    assert zs["c"] == (3 - 2) / sd
    assert abs(sum(zs.values())) < 1e-9  # z-scores sum to ~0


def test_zscore_zero_variance_is_zero():
    assert _zscores({"a": 5.0, "b": 5.0}) == {"a": 0.0, "b": 0.0}


def test_value_transform_nse_value50():
    assert _value_from_avgz(0.5) == 1.5              # (1+z)
    assert _value_from_avgz(2.0) == 3.0
    assert _value_from_avgz(-1.0) == 0.5             # 1/(1-z)
    assert _value_from_avgz(0.0) == 1.0              # boundary


def test_cheaper_stock_ranks_higher():
    # CHEAP: low PE/PB, high sales/mcap, high div. EXPENSIVE: opposite.
    rows = [
        {"ticker": "CHEAP", "pe": 5, "pb": 0.8, "sales": 900, "market_cap": 1000, "dividend_yield": 6},
        {"ticker": "MID", "pe": 20, "pb": 3, "sales": 500, "market_cap": 1000, "dividend_yield": 2},
        {"ticker": "RICH", "pe": 60, "pb": 12, "sales": 100, "market_cap": 1000, "dividend_yield": 0},
    ]
    out = score(rows)
    by = {r["ticker"]: r for r in out}
    assert by["CHEAP"]["rank"] == 1
    assert by["RICH"]["rank"] == 3
    assert by["CHEAP"]["value_score"] > by["RICH"]["value_score"]
    # every ranked row carries an alt (3-factor) rank too
    assert all(r.get("alt_rank") for r in out)


def test_missing_factor_averages_over_rest_not_fabricated():
    # NODIV has no dividend yield -> scored on the 3 factors it has, not dropped.
    rows = [
        {"ticker": "NODIV", "pe": 8, "pb": 1, "sales": 700, "market_cap": 1000, "dividend_yield": None},
        {"ticker": "FULL", "pe": 8, "pb": 1, "sales": 700, "market_cap": 1000, "dividend_yield": 3},
    ]
    out = score(rows)
    tickers = {r["ticker"] for r in out}
    assert tickers == {"NODIV", "FULL"}


def test_zero_valid_factors_dropped():
    rows = [
        {"ticker": "GOOD", "pe": 10, "pb": 2, "sales": 500, "market_cap": 1000, "dividend_yield": 1},
        {"ticker": "LOSS", "pe": -5, "pb": -1, "sales": 0, "market_cap": 0, "dividend_yield": None},
    ]
    out = score(rows)
    assert {r["ticker"] for r in out} == {"GOOD"}
