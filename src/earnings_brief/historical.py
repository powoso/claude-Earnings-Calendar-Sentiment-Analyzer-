"""Fetch historical earnings reactions using yfinance."""

from __future__ import annotations

import logging
from datetime import date, timedelta

import yfinance as yf

from earnings_brief.models import HistoricalReaction

logger = logging.getLogger(__name__)


def get_historical_reactions(ticker: str, num_quarters: int = 8) -> list[HistoricalReaction]:
    """Return past *num_quarters* earnings reactions for *ticker*.

    Each reaction includes the EPS surprise and the next-trading-day move.
    """
    try:
        tk = yf.Ticker(ticker)
        return _build_reactions(tk, num_quarters)
    except Exception:
        logger.debug("Historical reactions failed for %s", ticker, exc_info=True)
        return []


def _build_reactions(tk: yf.Ticker, num_quarters: int) -> list[HistoricalReaction]:
    """Combine earnings history with price data to compute post-earnings moves."""
    earnings_hist = _get_earnings_history(tk)
    if not earnings_hist:
        return []

    # Limit to the most recent quarters.
    earnings_hist = earnings_hist[-num_quarters:]

    # Grab ~3 years of daily price data so we can look up next-day moves.
    hist = tk.history(period="3y", auto_adjust=True)
    if hist is None or hist.empty:
        return []

    reactions: list[HistoricalReaction] = []
    for entry in earnings_hist:
        report_date = entry.get("date")
        eps_actual = entry.get("actual")
        eps_estimate = entry.get("estimate")
        quarter = entry.get("quarter", "")

        surprise_pct = None
        if eps_actual is not None and eps_estimate is not None and eps_estimate != 0:
            surprise_pct = round(((eps_actual - eps_estimate) / abs(eps_estimate)) * 100, 2)

        next_day_move = _compute_next_day_move(hist, report_date)

        reactions.append(HistoricalReaction(
            quarter=quarter,
            report_date=report_date,
            eps_actual=eps_actual,
            eps_estimate=eps_estimate,
            surprise_pct=surprise_pct,
            next_day_move_pct=next_day_move,
        ))

    reactions.reverse()  # Most recent first.
    return reactions


def _get_earnings_history(tk: yf.Ticker) -> list[dict]:
    """Extract earnings history from yfinance Ticker."""
    results: list[dict] = []

    # Try the earnings_dates attribute first (more reliable in newer yfinance).
    try:
        ed = tk.earnings_dates
        if ed is not None and not ed.empty:
            for idx, row in ed.iterrows():
                report_date = idx.date() if hasattr(idx, "date") else None
                eps_actual = _safe_float(row.get("Reported EPS"))
                eps_estimate = _safe_float(row.get("EPS Estimate"))
                # Only include past quarters with actual data.
                if eps_actual is not None and report_date and report_date < date.today():
                    q_label = _quarter_label(report_date)
                    results.append({
                        "date": report_date,
                        "actual": eps_actual,
                        "estimate": eps_estimate,
                        "quarter": q_label,
                    })
            if results:
                results.sort(key=lambda x: x["date"])
                return results
    except Exception:
        logger.debug("earnings_dates failed, falling back", exc_info=True)

    # Fallback: quarterly_earnings.
    try:
        qe = tk.quarterly_earnings
        if qe is not None and not qe.empty:
            for idx, row in qe.iterrows():
                results.append({
                    "date": None,
                    "actual": _safe_float(row.get("Actual")),
                    "estimate": _safe_float(row.get("Estimate")),
                    "quarter": str(idx),
                })
            return results
    except Exception:
        logger.debug("quarterly_earnings fallback also failed", exc_info=True)

    return results


def _compute_next_day_move(hist, report_date: date | None) -> float | None:
    """Compute the close-to-close % move on the first trading day after *report_date*."""
    if report_date is None or hist.empty:
        return None

    try:
        # Find the last close on or before report_date and the next close after.
        dates = hist.index
        before = dates[dates <= str(report_date)]
        after = dates[dates > str(report_date)]

        if before.empty or after.empty:
            return None

        close_before = float(hist.loc[before[-1], "Close"])
        close_after = float(hist.loc[after[0], "Close"])

        if close_before == 0:
            return None

        return round(((close_after - close_before) / close_before) * 100, 2)
    except Exception:
        logger.debug("next-day move calc failed for %s", report_date, exc_info=True)
        return None


def _quarter_label(d: date) -> str:
    """Return e.g. 'Q3 2024' for a given date."""
    q = (d.month - 1) // 3 + 1
    return f"Q{q} {d.year}"


def _safe_float(val) -> float | None:
    """Convert a value to float if possible, otherwise None."""
    if val is None:
        return None
    try:
        import math
        f = float(val)
        if math.isnan(f):
            return None
        return f
    except (TypeError, ValueError):
        return None
