"""Scrape social sentiment for a ticker from Reddit and StockTwits."""

from __future__ import annotations

import logging
import os
import re

import requests

from earnings_brief.models import SentimentData

logger = logging.getLogger(__name__)

_TIMEOUT = 15
_HEADERS = {
    "User-Agent": "earnings-brief/1.0",
}

# Simple keyword-based sentiment scoring.
_BULLISH_WORDS = {
    "bullish", "moon", "buy", "calls", "long", "breakout", "beat",
    "upgrade", "strong", "growth", "rocket", "undervalued", "upside",
    "accumulate", "outperform", "catalyst", "promising", "positive",
}
_BEARISH_WORDS = {
    "bearish", "sell", "puts", "short", "crash", "miss", "downgrade",
    "weak", "decline", "dump", "overvalued", "downside", "risk",
    "underperform", "negative", "warning", "trouble", "cut",
}


def get_social_sentiment(ticker: str, max_posts: int = 50) -> SentimentData:
    """Aggregate social sentiment for *ticker* across available sources."""
    posts: list[str] = []
    sources: list[str] = []

    reddit_posts = _from_reddit(ticker, max_posts)
    if reddit_posts:
        posts.extend(reddit_posts)
        sources.append("Reddit")

    stocktwits_posts = _from_stocktwits(ticker, max_posts)
    if stocktwits_posts:
        posts.extend(stocktwits_posts)
        sources.append("StockTwits")

    if not posts:
        return SentimentData(ticker=ticker, sources=sources)

    bullish = 0
    bearish = 0
    neutral = 0

    for post in posts:
        score = _score_text(post)
        if score > 0:
            bullish += 1
        elif score < 0:
            bearish += 1
        else:
            neutral += 1

    total = bullish + bearish + neutral
    overall = (bullish - bearish) / total if total > 0 else 0.0

    return SentimentData(
        ticker=ticker,
        overall_score=round(overall, 3),
        bullish_count=bullish,
        bearish_count=bearish,
        neutral_count=neutral,
        sample_posts=posts[:10],
        sources=sources,
    )


# ---------------------------------------------------------------------------
# Reddit via PRAW (optional)
# ---------------------------------------------------------------------------

def _from_reddit(ticker: str, limit: int) -> list[str]:
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    if not client_id or not client_secret:
        return _from_reddit_json(ticker, limit)

    try:
        import praw  # noqa: F811

        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=os.environ.get("REDDIT_USER_AGENT", "earnings-brief/1.0"),
        )
        posts: list[str] = []
        for subreddit_name in ("wallstreetbets", "stocks", "investing", "options"):
            try:
                sub = reddit.subreddit(subreddit_name)
                for submission in sub.search(ticker, sort="new", time_filter="week", limit=limit // 4):
                    text = f"{submission.title} {submission.selftext[:300]}"
                    posts.append(text.strip())
            except Exception:
                logger.debug("Reddit sub %s failed", subreddit_name, exc_info=True)
        return posts
    except Exception:
        logger.debug("PRAW-based Reddit scrape failed for %s", ticker, exc_info=True)
        return []


def _from_reddit_json(ticker: str, limit: int) -> list[str]:
    """Fallback: scrape Reddit JSON endpoints without authentication."""
    posts: list[str] = []
    for sub in ("wallstreetbets", "stocks", "investing"):
        try:
            url = f"https://www.reddit.com/r/{sub}/search.json"
            resp = requests.get(
                url,
                params={"q": ticker, "sort": "new", "t": "week", "limit": limit // 3, "restrict_sr": "on"},
                headers={"User-Agent": "earnings-brief/1.0"},
                timeout=_TIMEOUT,
            )
            if resp.status_code != 200:
                continue
            data = resp.json()
            for child in data.get("data", {}).get("children", []):
                d = child.get("data", {})
                text = f"{d.get('title', '')} {d.get('selftext', '')[:300]}"
                posts.append(text.strip())
        except Exception:
            logger.debug("Reddit JSON fallback failed for %s on r/%s", ticker, sub, exc_info=True)
    return posts


# ---------------------------------------------------------------------------
# StockTwits
# ---------------------------------------------------------------------------

def _from_stocktwits(ticker: str, limit: int) -> list[str]:
    try:
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        if resp.status_code != 200:
            return []
        data = resp.json()
        posts: list[str] = []
        for msg in data.get("messages", [])[:limit]:
            body = msg.get("body", "")
            posts.append(body)
        return posts
    except Exception:
        logger.debug("StockTwits scrape failed for %s", ticker, exc_info=True)
        return []


# ---------------------------------------------------------------------------
# Keyword sentiment scoring
# ---------------------------------------------------------------------------

def _score_text(text: str) -> int:
    """Return +1 (bullish), -1 (bearish), or 0 (neutral)."""
    words = set(re.findall(r"[a-z]+", text.lower()))
    bull_hits = len(words & _BULLISH_WORDS)
    bear_hits = len(words & _BEARISH_WORDS)
    if bull_hits > bear_hits:
        return 1
    if bear_hits > bull_hits:
        return -1
    return 0
