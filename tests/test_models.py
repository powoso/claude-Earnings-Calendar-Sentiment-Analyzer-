"""Tests for the data models."""

from datetime import date, datetime, timezone

from earnings_brief.models import (
    EarningsBrief,
    EarningsEvent,
    HistoricalReaction,
    NewsHeadline,
    SentimentData,
    TickerResearch,
)


def test_earnings_event_defaults():
    event = EarningsEvent(
        ticker="AAPL",
        company_name="Apple Inc.",
        earnings_date=date(2025, 1, 30),
    )
    assert event.ticker == "AAPL"
    assert event.time_of_day == "unknown"
    assert event.eps_estimate is None
    assert event.revenue_estimate is None


def test_news_headline():
    h = NewsHeadline(
        title="Apple beats estimates",
        source="Reuters",
        url="https://example.com/article",
        published=datetime(2025, 1, 28, 14, 0, tzinfo=timezone.utc),
        snippet="Apple reported Q1 earnings above expectations.",
    )
    assert h.title == "Apple beats estimates"
    assert h.published is not None


def test_sentiment_data_defaults():
    s = SentimentData(ticker="AAPL")
    assert s.overall_score == 0.0
    assert s.bullish_count == 0
    assert s.sample_posts == []
    assert s.sources == []


def test_historical_reaction():
    r = HistoricalReaction(
        quarter="Q4 2024",
        report_date=date(2024, 10, 31),
        eps_actual=1.64,
        eps_estimate=1.60,
        surprise_pct=2.5,
        next_day_move_pct=3.2,
    )
    assert r.surprise_pct == 2.5
    assert r.next_day_move_pct == 3.2


def test_ticker_research_assembly():
    event = EarningsEvent(ticker="MSFT", company_name="Microsoft", earnings_date=date(2025, 1, 28))
    research = TickerResearch(event=event)
    assert research.headlines == []
    assert research.sentiment is None
    assert research.historical_reactions == []


def test_earnings_brief():
    brief = EarningsBrief(
        ticker="NVDA",
        company_name="NVIDIA",
        earnings_date=date(2025, 2, 26),
        expected_move="±8%",
        full_brief="Full analysis text…",
    )
    assert brief.expected_move == "±8%"
    assert brief.key_risks == ""
