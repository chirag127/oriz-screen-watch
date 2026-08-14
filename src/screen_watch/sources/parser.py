"""screener.in company-page fundamentals parser (SSR HTML — no auth, no browser).

VERIFIED 2026-08-14 against the LIVE https://www.screener.in/company/TCS/ page
(httpx GET, 200, server-rendered). The top ratio block is:

    <ul id="top-ratios">
      <li ...><span class="name">Market Cap</span>
              <span class="nowrap value"><span class="number">8,51,517</span> Cr.</span></li>
      <li ...><span class="name">Current Price</span> ... </li>
      ... Stock P/E · Book Value · Dividend Yield · ROCE · ROE · High / Low · Face Value
    </ul>

Each <li> = one ratio: `.name` label + `.value` text. We normalise the label,
strip ₹/%/Cr./commas and parse the number. Price-to-book is NOT a printed row —
we DERIVE it: pb = current_price / book_value (both parsed). NEVER fabricate:
a ratio absent from the block => None.
"""

from __future__ import annotations

import logging
import re

from selectolax.parser import HTMLParser

log = logging.getLogger("screen_watch")

# label (normalised: lowercased, non-alnum -> space, collapsed) -> field
_LABEL_MAP = {
    "market cap": "market_cap",
    "current price": "current_price",
    "stock p e": "pe",
    "book value": "book_value",
    "dividend yield": "dividend_yield",
    "roce": "roce",
    "roe": "roe",
    "face value": "face_value",
    "high low": "_high_low",   # "3,350 / 1,976" -> high, low
    "sales": "sales",
    "price to book value": "pb",
}


def _norm_label(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", s.lower())).strip()


def _num(s: str) -> float | None:
    """First numeric token in `s` (handles ₹, %, Cr., commas). None if absent."""
    if s is None:
        return None
    m = re.search(r"-?\d[\d,]*\.?\d*", s.replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None


def parse_company(html: str, ticker: str) -> dict:
    """Parse the top-ratio block from a screener.in company page.

    Returns a dict with every known ratio (missing => None) plus a derived
    `pb` (current_price / book_value) and the parsed company `name`."""
    tree = HTMLParser(html)
    out: dict[str, float | str | None] = {
        "ticker": ticker.strip().upper(),
        "name": None,
        "market_cap": None, "current_price": None, "pe": None,
        "book_value": None, "dividend_yield": None, "roce": None, "roe": None,
        "face_value": None, "high": None, "low": None, "sales": None, "pb": None,
    }

    h1 = tree.css_first("h1")
    if h1:
        out["name"] = h1.text(strip=True)

    block = tree.css_first("#top-ratios")
    if block is None:
        log.warning("parse %s: no #top-ratios block", ticker)
        return out

    for li in block.css("li"):
        name_el = li.css_first(".name")
        val_el = li.css_first(".value")
        if not name_el or not val_el:
            continue
        field = _LABEL_MAP.get(_norm_label(name_el.text(strip=True)))
        if not field:
            continue
        raw = val_el.text(separator=" ", strip=True)
        if field == "_high_low":
            parts = raw.split("/")
            out["high"] = _num(parts[0]) if len(parts) > 0 else None
            out["low"] = _num(parts[1]) if len(parts) > 1 else None
        else:
            out[field] = _num(raw)

    # derive P/B when the row isn't printed (screener rarely prints it for NSE)
    if out.get("pb") is None:
        cp, bv = out.get("current_price"), out.get("book_value")
        if isinstance(cp, (int, float)) and isinstance(bv, (int, float)) and bv > 0:
            out["pb"] = round(cp / bv, 2)

    return out
