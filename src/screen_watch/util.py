"""Shared helpers: keyless HTTP fetch (browser-parity headers) + logging."""

from __future__ import annotations

import logging
import sys

import httpx

from . import config as C

log = logging.getLogger("screen_watch")


def configure_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )


def fetch_text(url: str, timeout: float | None = None) -> str:
    headers = {
        "User-Agent": C.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    with httpx.Client(headers=headers, timeout=timeout or C.REQUEST_TIMEOUT,
                      follow_redirects=True) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.text
