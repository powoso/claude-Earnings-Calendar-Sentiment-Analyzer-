# Earnings Calendar Sentiment Analyzer

A CLI tool that pulls upcoming earnings dates, scrapes recent news headlines and social sentiment for each ticker, and uses Claude to generate a pre-earnings brief with expected move, analyst consensus, key risks, and historical earnings reactions.

## Architecture

```
src/earnings_brief/
├── cli.py                 # Rich CLI interface (scan / brief / calendar)
├── orchestrator.py        # Main pipeline — wires all modules together
├── earnings_calendar.py   # Fetches upcoming earnings dates via yfinance
├── news_scraper.py        # Scrapes headlines from Google/Yahoo RSS, Finviz, NewsAPI
├── sentiment.py           # Social sentiment from Reddit & StockTwits
├── historical.py          # Historical earnings reactions & post-earnings moves
├── brief_generator.py     # Claude-powered brief generation
└── models.py              # Shared dataclasses
```

## Quick Start

### 1. Install

```bash
pip install -e .
```

### 2. Set your API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. Run

```bash
# Generate a brief for a single ticker
earnings-brief brief AAPL

# Scan the default watchlist (30 large-caps) for upcoming earnings
earnings-brief scan

# Scan specific tickers, looking 30 days ahead
earnings-brief scan --days 30 AAPL MSFT NVDA GOOGL

# Just show the earnings calendar
earnings-brief calendar
earnings-brief calendar --days 30 AAPL MSFT NVDA
```

## Commands

| Command    | Description |
|------------|-------------|
| `brief <TICKER>` | Generate a full pre-earnings brief for one ticker |
| `scan [TICKERS...]` | Find upcoming earnings and generate briefs for each |
| `calendar [TICKERS...]` | Display a table of upcoming earnings dates |

### Common Options

| Flag | Description |
|------|-------------|
| `--days N` | Look-ahead window in days (default: 14) |
| `--model MODEL` | Claude model to use (default: `claude-sonnet-4-6`) |
| `-o FILE` | Save briefs to a markdown file |
| `-v` | Verbose / debug logging |

## What's in a Brief?

Each brief contains:

1. **Expected Move** — Estimated post-earnings price move based on historical patterns
2. **Analyst Consensus** — EPS/revenue estimates, recent rating changes, price targets
3. **Key Risks** — Top 3-5 upside and downside risks heading into the report
4. **Historical Earnings Reactions** — Past beat/miss patterns and average moves
5. **Sentiment Summary** — Current social and news sentiment
6. **Bottom Line** — A 2-3 sentence actionable summary

## Data Sources

| Data | Source |
|------|--------|
| Earnings dates & estimates | Yahoo Finance (yfinance) |
| News headlines | Google News RSS, Yahoo Finance RSS, Finviz, NewsAPI (optional) |
| Social sentiment | Reddit (PRAW or JSON fallback), StockTwits |
| Historical reactions | Yahoo Finance earnings history + price data |
| Brief generation | Claude API (Anthropic) |

## Optional API Keys

Set these in your environment or a `.env` file for richer data:

```bash
# Reddit API (improves sentiment analysis)
export REDDIT_CLIENT_ID="..."
export REDDIT_CLIENT_SECRET="..."

# NewsAPI (additional news coverage)
export NEWSAPI_KEY="..."
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

## License

MIT
