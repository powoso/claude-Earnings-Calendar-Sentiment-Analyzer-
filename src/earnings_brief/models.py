"""Shared data models used across all modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class EarningsEvent:
    """A single upcoming earnings release."""

    ticker: str
    company_name: str
    earnings_date: date
    time_of_day: str = "unknown"  # "before_market", "after_market", "unknown"
    eps_estimate: float | None = None
    revenue_estimate: float | None = None


@dataclass
class NewsHeadline:
    """A scraped news headline related to a ticker."""

    title: str
    source: str
    url: str
    published: datetime | None = None
    snippet: str = ""


@dataclass
class SentimentData:
    """Aggregated sentiment signals for a ticker."""

    ticker: str
    overall_score: float = 0.0  # -1.0 (bearish) to 1.0 (bullish)
    bullish_count: int = 0
    bearish_count: int = 0
    neutral_count: int = 0
    sample_posts: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)


@dataclass
class HistoricalReaction:
    """Historical earnings reaction for a single quarter."""

    quarter: str  # e.g. "Q3 2024"
    report_date: date | None = None
    eps_actual: float | None = None
    eps_estimate: float | None = None
    surprise_pct: float | None = None
    next_day_move_pct: float | None = None


@dataclass
class TickerResearch:
    """All research data collected for a single ticker."""

    event: EarningsEvent
    headlines: list[NewsHeadline] = field(default_factory=list)
    sentiment: SentimentData | None = None
    historical_reactions: list[HistoricalReaction] = field(default_factory=list)


@dataclass
class EarningsBrief:
    """The final Claude-generated pre-earnings brief."""

    ticker: str
    company_name: str
    earnings_date: date
    expected_move: str = ""
    analyst_consensus: str = ""
    key_risks: str = ""
    historical_reactions_summary: str = ""
    sentiment_summary: str = ""
    full_brief: str = ""
