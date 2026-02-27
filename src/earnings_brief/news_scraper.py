"""Scrape recent news headlines for a ticker from multiple free sources."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import feedparser
import requests
from bs4 import BeautifulSoup

from earnings_brief.models import NewsHeadline

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}
_TIMEOUT = 15


def get_news_headlines(ticker: str, max_results: int = 15) -> list[NewsHeadline]:
    """Gather recent news headlines for *ticker* from multiple sources."""
    headlines: list[NewsHeadline] = []

    headlines.extend(_from_google_rss(ticker, max_results))
    headlines.extend(_from_yahoo_rss(ticker, max_results))
    headlines.extend(_from_newsapi(ticker, max_results))
    headlines.extend(_from_finviz(ticker, max_results))

    # Deduplicate by title (case-insensitive)
    seen: set[str] = set()
    unique: list[NewsHeadline] = []
    for h in headlines:
        key = h.title.lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(h)

    unique.sort(key=lambda h: h.published or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return unique[:max_results]


# ---------------------------------------------------------------------------
# Source: Google News RSS
# ---------------------------------------------------------------------------

def _from_google_rss(ticker: str, limit: int) -> list[NewsHeadline]:
    try:
        url = f"https://news.google.com/rss/search?q={ticker}+stock+earnings&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        results: list[NewsHeadline] = []
        for entry in feed.entries[:limit]:
            pub = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            results.append(NewsHeadline(
                title=entry.get("title", ""),
                source="Google News",
                url=entry.get("link", ""),
                published=pub,
                snippet=_strip_html(entry.get("summary", "")),
            ))
        return results
    except Exception:
        logger.debug("Google RSS scrape failed for %s", ticker, exc_info=True)
        return []


# ---------------------------------------------------------------------------
# Source: Yahoo Finance RSS
# ---------------------------------------------------------------------------

def _from_yahoo_rss(ticker: str, limit: int) -> list[NewsHeadline]:
    try:
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
        feed = feedparser.parse(url)
        results: list[NewsHeadline] = []
        for entry in feed.entries[:limit]:
            pub = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            results.append(NewsHeadline(
                title=entry.get("title", ""),
                source="Yahoo Finance",
                url=entry.get("link", ""),
                published=pub,
                snippet=_strip_html(entry.get("summary", "")),
            ))
        return results
    except Exception:
        logger.debug("Yahoo RSS scrape failed for %s", ticker, exc_info=True)
        return []


# ---------------------------------------------------------------------------
# Source: NewsAPI (optional, requires API key)
# ---------------------------------------------------------------------------

def _from_newsapi(ticker: str, limit: int) -> list[NewsHeadline]:
    api_key = os.environ.get("NEWSAPI_KEY")
    if not api_key:
        return []
    try:
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": f"{ticker} earnings",
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": limit,
                "apiKey": api_key,
            },
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        results: list[NewsHeadline] = []
        for article in data.get("articles", [])[:limit]:
            pub = None
            if article.get("publishedAt"):
                pub = datetime.fromisoformat(article["publishedAt"].replace("Z", "+00:00"))
            results.append(NewsHeadline(
                title=article.get("title", ""),
                source=article.get("source", {}).get("name", "NewsAPI"),
                url=article.get("url", ""),
                published=pub,
                snippet=article.get("description", ""),
            ))
        return results
    except Exception:
        logger.debug("NewsAPI scrape failed for %s", ticker, exc_info=True)
        return []


# ---------------------------------------------------------------------------
# Source: Finviz news table
# ---------------------------------------------------------------------------

def _from_finviz(ticker: str, limit: int) -> list[NewsHeadline]:
    try:
        url = f"https://finviz.com/quote.ashx?t={ticker}&p=d"
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        news_table = soup.find(id="news-table")
        if news_table is None:
            return []

        results: list[NewsHeadline] = []
        for row in news_table.find_all("tr")[:limit]:
            link_tag = row.find("a")
            if link_tag is None:
                continue
            title = link_tag.get_text(strip=True)
            href = link_tag.get("href", "")
            source_span = row.find("span", class_="news-link-right")
            source = source_span.get_text(strip=True) if source_span else "Finviz"
            results.append(NewsHeadline(
                title=title,
                source=source,
                url=href,
            ))
        return results
    except Exception:
        logger.debug("Finviz scrape failed for %s", ticker, exc_info=True)
        return []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_html(text: str) -> str:
    """Remove HTML tags from a string."""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ", strip=True)
