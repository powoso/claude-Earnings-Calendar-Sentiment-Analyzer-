"""Use Claude to synthesize research into a structured pre-earnings brief."""

from __future__ import annotations

import logging
import os
from datetime import date

from anthropic import Anthropic

from earnings_brief.models import EarningsBrief, TickerResearch

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "claude-sonnet-4-6"


def generate_brief(research: TickerResearch, model: str | None = None) -> EarningsBrief:
    """Call Claude to produce a comprehensive pre-earnings brief.

    Requires the ``ANTHROPIC_API_KEY`` environment variable to be set.
    """
    client = Anthropic()  # reads ANTHROPIC_API_KEY from env
    model = model or os.environ.get("CLAUDE_MODEL", _DEFAULT_MODEL)
    prompt = _build_prompt(research)

    message = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
        system=_SYSTEM_PROMPT,
    )

    full_text = message.content[0].text
    return _parse_response(research, full_text)


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are an expert equity research analyst specializing in pre-earnings analysis.
You produce concise, data-driven briefs that help traders and investors prepare
for upcoming earnings announcements. Always cite specific numbers and dates when
available. Be balanced — present both bull and bear cases."""


def _build_prompt(research: TickerResearch) -> str:
    """Assemble all research data into a structured prompt for Claude."""
    event = research.event
    sections: list[str] = []

    sections.append(f"""\
# Pre-Earnings Brief Request

**Ticker:** {event.ticker}
**Company:** {event.company_name}
**Earnings Date:** {event.earnings_date.isoformat()}
**Timing:** {event.time_of_day}
**EPS Estimate:** {_fmt(event.eps_estimate)}
**Revenue Estimate:** {_fmt_revenue(event.revenue_estimate)}
""")

    # News headlines
    if research.headlines:
        lines = ["## Recent News Headlines"]
        for h in research.headlines[:12]:
            pub = h.published.strftime("%Y-%m-%d") if h.published else "N/A"
            lines.append(f"- [{pub}] **{h.title}** ({h.source})")
            if h.snippet:
                lines.append(f"  _{h.snippet[:200]}_")
        sections.append("\n".join(lines))

    # Social sentiment
    if research.sentiment and research.sentiment.sources:
        s = research.sentiment
        sections.append(f"""\
## Social Sentiment
- **Overall Score:** {s.overall_score:+.2f} (-1 bearish → +1 bullish)
- **Bullish posts:** {s.bullish_count} | **Bearish:** {s.bearish_count} | **Neutral:** {s.neutral_count}
- **Sources:** {', '.join(s.sources)}

Sample posts:
{_bullet_list(s.sample_posts[:6])}""")

    # Historical reactions
    if research.historical_reactions:
        lines = ["## Historical Earnings Reactions (most recent first)"]
        lines.append("| Quarter | EPS Est | EPS Act | Surprise % | Next-Day Move |")
        lines.append("|---------|---------|---------|------------|---------------|")
        for r in research.historical_reactions[:8]:
            lines.append(
                f"| {r.quarter} "
                f"| {_fmt(r.eps_estimate)} "
                f"| {_fmt(r.eps_actual)} "
                f"| {_fmt_pct(r.surprise_pct)} "
                f"| {_fmt_pct(r.next_day_move_pct)} |"
            )
        sections.append("\n".join(lines))

    sections.append("""\
## Instructions

Based on ALL of the data above, generate a pre-earnings brief with these sections:

### 1. Expected Move
Estimate the implied or likely post-earnings move based on historical patterns,
current implied volatility context, and recent price action.

### 2. Analyst Consensus
Summarize what analysts and the market expect — EPS/revenue estimates, recent
rating changes, price target distribution.

### 3. Key Risks
List the top 3-5 risks heading into this earnings report (both upside and
downside risks).

### 4. Historical Earnings Reactions
Summarize the pattern of past earnings reactions — average move, beat/miss
frequency, any trends.

### 5. Sentiment Summary
Characterize the current market and social sentiment heading into the report.

### 6. Bottom Line
A 2-3 sentence verdict: what should a trader focus on heading into this print?

Format your response using the exact section headers above (### 1. Expected Move, etc.).""")

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def _parse_response(research: TickerResearch, text: str) -> EarningsBrief:
    """Split Claude's response into the brief's structured fields."""
    brief = EarningsBrief(
        ticker=research.event.ticker,
        company_name=research.event.company_name,
        earnings_date=research.event.earnings_date,
        full_brief=text,
    )

    brief.expected_move = _extract_section(text, "Expected Move")
    brief.analyst_consensus = _extract_section(text, "Analyst Consensus")
    brief.key_risks = _extract_section(text, "Key Risks")
    brief.historical_reactions_summary = _extract_section(text, "Historical Earnings Reactions")
    brief.sentiment_summary = _extract_section(text, "Sentiment Summary")

    return brief


def _extract_section(text: str, heading: str) -> str:
    """Extract text under a markdown ### heading."""
    import re

    # Match "### N. <heading>" or "### <heading>"
    pattern = rf"###\s*\d*\.?\s*{re.escape(heading)}\s*\n(.*?)(?=\n###|\Z)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt(val: float | None) -> str:
    return f"${val:.2f}" if val is not None else "N/A"


def _fmt_revenue(val: float | None) -> str:
    if val is None:
        return "N/A"
    if abs(val) >= 1e9:
        return f"${val / 1e9:.2f}B"
    if abs(val) >= 1e6:
        return f"${val / 1e6:.1f}M"
    return f"${val:,.0f}"


def _fmt_pct(val: float | None) -> str:
    return f"{val:+.1f}%" if val is not None else "N/A"


def _bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item[:200]}" for item in items) if items else "_(none)_"
