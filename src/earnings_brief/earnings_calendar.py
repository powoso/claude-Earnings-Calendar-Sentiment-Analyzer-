"""Fetch upcoming earnings dates from Yahoo Finance via yfinance."""

from __future__ import annotations

import logging
from datetime import date, timedelta

import yfinance as yf

from earnings_brief.models import EarningsEvent

logger = logging.getLogger(__name__)

# Well-known large-cap tickers used as a default watchlist.
DEFAULT_WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
    "JPM", "V", "JNJ", "WMT", "PG", "MA", "UNH", "HD",
    "DIS", "NFLX", "PYPL", "CRM", "INTC", "AMD", "COST",
    "PEP", "ABBV", "KO", "MRK", "TMO", "CSCO", "ORCL", "NKE",
]


def get_upcoming_earnings(
    tickers: list[str] | None = None,
    days_ahead: int = 14,
) -> list[EarningsEvent]:
    """Return earnings events within *days_ahead* days for the given tickers.

    If *tickers* is ``None`` the ``DEFAULT_WATCHLIST`` is used.
    """
    tickers = tickers or DEFAULT_WATCHLIST
    cutoff = date.today() + timedelta(days=days_ahead)
    events: list[EarningsEvent] = []

    for symbol in tickers:
        try:
            event = _fetch_single(symbol, cutoff)
            if event is not None:
                events.append(event)
        except Exception:
            logger.debug("Could not fetch earnings for %s", symbol, exc_info=True)

    events.sort(key=lambda e: e.earnings_date)
    return events


def _fetch_single(symbol: str, cutoff: date) -> EarningsEvent | None:
    """Fetch earnings info for a single ticker."""
    tk = yf.Ticker(symbol)
    cal = tk.calendar
    if cal is None or (hasattr(cal, "empty") and cal.empty):
        return None

    # yfinance returns calendar as a dict or DataFrame depending on version.
    earnings_date_val = _extract_date(cal)
    if earnings_date_val is None or earnings_date_val > cutoff or earnings_date_val < date.today():
        return None

    info = tk.info or {}
    company_name = info.get("shortName") or info.get("longName") or symbol

    eps_est = _safe_float(cal, "Earnings Average")
    rev_est = _safe_float(cal, "Revenue Average")

    return EarningsEvent(
        ticker=symbol,
        company_name=company_name,
        earnings_date=earnings_date_val,
        eps_estimate=eps_est,
        revenue_estimate=rev_est,
    )


def _extract_date(cal) -> date | None:
    """Pull the earnings date out of the calendar object."""
    if isinstance(cal, dict):
        raw = cal.get("Earnings Date")
        if isinstance(raw, list) and raw:
            raw = raw[0]
        if raw is None:
            return None
        if isinstance(raw, date):
            return raw
        if hasattr(raw, "date"):
            return raw.date()
        return None

    # DataFrame path
    try:
        raw = cal.loc["Earnings Date"]
        if hasattr(raw, "iloc"):
            raw = raw.iloc[0]
        if hasattr(raw, "date"):
            return raw.date()
        if isinstance(raw, date):
            return raw
    except (KeyError, IndexError):
        pass
    return None


def _safe_float(cal, key: str) -> float | None:
    """Safely extract a float value from a calendar dict/DataFrame."""
    try:
        if isinstance(cal, dict):
            val = cal.get(key)
        else:
            val = cal.loc[key]
            if hasattr(val, "iloc"):
                val = val.iloc[0]
        if val is not None:
            return float(val)
    except (KeyError, IndexError, TypeError, ValueError):
        pass
    return None
