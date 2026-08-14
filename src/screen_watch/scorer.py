"""Value-score engine — Nifty500 Value 50 methodology (VERIFIED from NSE Indices).

PRIMARY (Value 50 replica) — 4 equal-weight (0.25) cheapness factors:
  E/P    = 1/PE       earnings-to-price
  B/P    = 1/PB       book-to-price
  S/P    = sales/mcap sales-to-price
  DivYld = dividend yield (as-is, already a yield)

Each factor is converted to a CROSS-SECTIONAL Z-SCORE across the tracked
universe. A stock's raw value = mean of its available factor z-scores
(missing a factor => averaged over the rest; a factor needs a valid + positive
ratio: PE/PB/S-P > 0, DivYld >= 0). Per NSE Value 50:
  ValueScore = (1 + avgZ)      if avgZ > 0
             = (1 - avgZ)^-1    if avgZ <= 0
Higher score = cheaper/better value. Stocks rank by score, descending.

ALTERNATE (BSE Enhanced Value style) — same construction over 3 factors only
(E/P, B/P, S/P — NO dividend yield), giving a second ranking `alt_rank`.

NEVER fabricate: a stock with zero valid value factors is dropped from the rank.
"""

from __future__ import annotations

import logging
import math

log = logging.getLogger("screen_watch")

# (field, mode): "inv" => 1/ratio (positive-only) · "raw" => value as-is (>=0)
_PRIMARY = {"ep": "inv", "bp": "inv", "sp": "sp", "div": "raw"}
_ALT = {"ep": "inv", "bp": "inv", "sp": "sp"}


def _zscores(values: dict[str, float]) -> dict[str, float]:
    """Population cross-sectional z-score over the provided values."""
    n = len(values)
    if n == 0:
        return {}
    mean = sum(values.values()) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in values.values()) / n)
    if sd == 0:
        return {k: 0.0 for k in values}
    return {k: (v - mean) / sd for k, v in values.items()}


def _factor_yields(row: dict) -> dict[str, float]:
    """Cheapness yield per factor for one stock (only valid+positive)."""
    pe, pb = row.get("pe"), row.get("pb")
    sales, mcap = row.get("sales"), row.get("market_cap")
    div = row.get("dividend_yield")
    y: dict[str, float] = {}
    if isinstance(pe, (int, float)) and pe > 0:
        y["ep"] = 1.0 / pe
    if isinstance(pb, (int, float)) and pb > 0:
        y["bp"] = 1.0 / pb
    if (isinstance(sales, (int, float)) and sales > 0
            and isinstance(mcap, (int, float)) and mcap > 0):
        y["sp"] = sales / mcap
    if isinstance(div, (int, float)) and div >= 0:
        y["div"] = div
    return y


def _value_from_avgz(avg_z: float) -> float:
    """NSE Value 50 transform: (1+z) if z>0 else 1/(1-z)."""
    return (1.0 + avg_z) if avg_z > 0 else 1.0 / (1.0 - avg_z)


def _score_universe(rows: list[dict], factors: dict[str, str], key: str) -> dict[str, float]:
    """Compute {ticker: ValueScore} for `rows` over the given factor set."""
    # per-factor yields for every stock, then per-factor cross-sectional z-scores
    per_factor: dict[str, dict[str, float]] = {f: {} for f in factors}
    all_yields = {r["ticker"]: _factor_yields(r) for r in rows}
    for t, ys in all_yields.items():
        for f in factors:
            if f in ys:
                per_factor[f][t] = ys[f]
    zs = {f: _zscores(per_factor[f]) for f in factors}

    scores: dict[str, float] = {}
    for r in rows:
        t = r["ticker"]
        fz = [zs[f][t] for f in factors if t in zs[f]]
        if not fz:
            continue
        scores[t] = _value_from_avgz(sum(fz) / len(fz))
    return scores


def _r(v, nd: int = 2):
    return round(v, nd) if isinstance(v, (int, float)) else None


def score(rows: list[dict]) -> list[dict]:
    """Rank the universe by the Value-50 composite (primary) with a BSE-Enhanced
    3-factor alternate ranking. Returns enriched rows sorted by primary rank
    (best value first). Rows with zero valid value factors are dropped."""
    primary = _score_universe(rows, _PRIMARY, "value_score")
    alt = _score_universe(rows, _ALT, "alt_value_score")

    out: list[dict] = []
    for r in rows:
        t = r["ticker"]
        if t not in primary:
            continue
        out.append({
            "ticker": t,
            "name": r.get("name"),
            "current_price": _r(r.get("current_price")),
            "market_cap": _r(r.get("market_cap")),
            "pe": _r(r.get("pe")),
            "pb": _r(r.get("pb")),
            "book_value": _r(r.get("book_value")),
            "dividend_yield": _r(r.get("dividend_yield")),
            "roce": _r(r.get("roce")),
            "roe": _r(r.get("roe")),
            "sales": _r(r.get("sales")),
            "high": _r(r.get("high")),
            "low": _r(r.get("low")),
            "face_value": _r(r.get("face_value")),
            "value_score": round(primary[t], 4),
            "alt_value_score": round(alt[t], 4) if t in alt else None,
        })

    out.sort(key=lambda x: x["value_score"], reverse=True)
    for i, row in enumerate(out, 1):
        row["rank"] = i
    alt_ranked = sorted(
        [x for x in out if x["alt_value_score"] is not None],
        key=lambda x: x["alt_value_score"], reverse=True,
    )
    for i, row in enumerate(alt_ranked, 1):
        row["alt_rank"] = i
    log.info("scored %d/%d stocks (>=1 valid value factor)", len(out), len(rows))
    return out
