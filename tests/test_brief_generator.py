"""Tests for prompt building and response parsing."""

from datetime import date

from earnings_brief.brief_generator import _build_prompt, _extract_section, _fmt, _fmt_pct, _fmt_revenue
from earnings_brief.models import (
    EarningsEvent,
    HistoricalReaction,
    NewsHeadline,
    SentimentData,
    TickerResearch,
)


def _make_research() -> TickerResearch:
    event = EarningsEvent(
        ticker="AAPL",
        company_name="Apple Inc.",
        earnings_date=date(2025, 1, 30),
        eps_estimate=2.35,
        revenue_estimate=124_000_000_000,
    )
    return TickerResearch(
        event=event,
        headlines=[
            NewsHeadline(title="Apple set to report Q1", source="CNBC", url="https://example.com"),
        ],
        sentiment=SentimentData(
            ticker="AAPL",
            overall_score=0.35,
            bullish_count=40,
            bearish_count=15,
            neutral_count=20,
            sources=["Reddit", "StockTwits"],
        ),
        historical_reactions=[
            HistoricalReaction(quarter="Q4 2024", eps_actual=1.64, eps_estimate=1.60, surprise_pct=2.5, next_day_move_pct=3.2),
        ],
    )


def test_build_prompt_includes_ticker():
    research = _make_research()
    prompt = _build_prompt(research)
    assert "AAPL" in prompt
    assert "Apple Inc." in prompt


def test_build_prompt_includes_headlines():
    research = _make_research()
    prompt = _build_prompt(research)
    assert "Apple set to report Q1" in prompt


def test_build_prompt_includes_sentiment():
    research = _make_research()
    prompt = _build_prompt(research)
    assert "+0.35" in prompt
    assert "Reddit" in prompt


def test_build_prompt_includes_historical():
    research = _make_research()
    prompt = _build_prompt(research)
    assert "Q4 2024" in prompt
    assert "+2.5%" in prompt


def test_extract_section():
    text = """### 1. Expected Move
About ±5% based on historical data.

### 2. Analyst Consensus
Analysts expect a beat.

### 3. Key Risks
- Supply chain
- China revenue"""
    assert "±5%" in _extract_section(text, "Expected Move")
    assert "Analysts expect" in _extract_section(text, "Analyst Consensus")
    assert "Supply chain" in _extract_section(text, "Key Risks")


def test_extract_section_missing():
    assert _extract_section("No sections here", "Expected Move") == ""


def test_fmt():
    assert _fmt(1.23) == "$1.23"
    assert _fmt(None) == "N/A"


def test_fmt_revenue():
    assert _fmt_revenue(124_000_000_000) == "$124.00B"
    assert _fmt_revenue(500_000_000) == "$500.0M"
    assert _fmt_revenue(None) == "N/A"


def test_fmt_pct():
    assert _fmt_pct(3.2) == "+3.2%"
    assert _fmt_pct(-1.5) == "-1.5%"
    assert _fmt_pct(None) == "N/A"
