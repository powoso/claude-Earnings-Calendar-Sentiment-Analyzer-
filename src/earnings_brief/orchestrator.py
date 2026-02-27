"""Main orchestrator — wires together all modules to produce briefs."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from earnings_brief.brief_generator import generate_brief
from earnings_brief.earnings_calendar import get_upcoming_earnings
from earnings_brief.historical import get_historical_reactions
from earnings_brief.models import EarningsBrief, EarningsEvent, TickerResearch
from earnings_brief.news_scraper import get_news_headlines
from earnings_brief.sentiment import get_social_sentiment

logger = logging.getLogger(__name__)


def run_pipeline(
    tickers: list[str] | None = None,
    days_ahead: int = 14,
    model: str | None = None,
    max_workers: int = 4,
) -> list[EarningsBrief]:
    """End-to-end pipeline: discover earnings → research → generate briefs."""
    events = get_upcoming_earnings(tickers=tickers, days_ahead=days_ahead)
    if not events:
        logger.info("No upcoming earnings found within %d days", days_ahead)
        return []

    logger.info("Found %d upcoming earnings events", len(events))
    briefs: list[EarningsBrief] = []

    for event in events:
        try:
            research = research_ticker(event, max_workers=max_workers)
            brief = generate_brief(research, model=model)
            briefs.append(brief)
        except Exception:
            logger.error("Failed to generate brief for %s", event.ticker, exc_info=True)

    return briefs


def run_single(
    ticker: str,
    model: str | None = None,
    max_workers: int = 4,
) -> EarningsBrief:
    """Generate a brief for a single ticker (regardless of earnings date)."""
    from datetime import date

    event = _get_or_build_event(ticker)
    research = research_ticker(event, max_workers=max_workers)
    return generate_brief(research, model=model)


def research_ticker(
    event: EarningsEvent,
    max_workers: int = 4,
) -> TickerResearch:
    """Gather all research data for a single ticker in parallel."""
    research = TickerResearch(event=event)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(get_news_headlines, event.ticker): "headlines",
            pool.submit(get_social_sentiment, event.ticker): "sentiment",
            pool.submit(get_historical_reactions, event.ticker): "historical",
        }
        for future in as_completed(futures):
            label = futures[future]
            try:
                result = future.result()
                if label == "headlines":
                    research.headlines = result
                elif label == "sentiment":
                    research.sentiment = result
                elif label == "historical":
                    research.historical_reactions = result
            except Exception:
                logger.warning("Research step '%s' failed for %s", label, event.ticker, exc_info=True)

    return research


def _get_or_build_event(ticker: str) -> EarningsEvent:
    """Try to fetch the real earnings event; fall back to a stub."""
    from datetime import date, timedelta

    events = get_upcoming_earnings(tickers=[ticker], days_ahead=90)
    if events:
        return events[0]

    # Build a minimal stub so single-ticker mode still works.
    import yfinance as yf

    tk = yf.Ticker(ticker)
    info = tk.info or {}
    name = info.get("shortName") or info.get("longName") or ticker

    return EarningsEvent(
        ticker=ticker,
        company_name=name,
        earnings_date=date.today(),
    )
