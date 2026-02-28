# Earnings Calendar Sentiment Analyzer

A beautiful web dashboard and CLI tool that pulls upcoming earnings dates, scrapes recent news headlines and social sentiment for each ticker, and uses Claude to generate a pre-earnings brief with expected move, analyst consensus, key risks, and historical earnings reactions.

## Features

- **Beautiful Web Dashboard** — Dark-themed financial UI with glass-morphism cards, Plotly charts, and smooth animations
- **Streamlit Dashboard** — Alternative lightweight dashboard interface
- **Earnings Calendar** — Scan 30+ large-cap tickers for upcoming earnings within a configurable date range
- **Multi-Source News** — Headlines aggregated from Google News, Yahoo Finance, Finviz, and NewsAPI
- **Social Sentiment** — Bullish/bearish scoring from Reddit (r/wallstreetbets, r/stocks, r/investing) and StockTwits
- **Historical Reactions** — Past 8 quarters of EPS surprises and next-day price moves with interactive charts
- **Claude-Powered Briefs** — AI-generated pre-earnings analysis covering expected move, consensus, risks, and sentiment
- **Rich CLI** — Terminal interface with scan, brief, and calendar commands
- **Export** — Download briefs as Markdown files from the UI or CLI

## Web App

The Flask-based web app provides a polished, Bloomberg-inspired dark-themed interface:

**Dashboard (`/`)**
- Hero section with animated gradient background
- Watchlist presets: Top 30 Large-Caps, Magnificent 7, FAANG+, Semiconductors, Finance, or Custom
- Date range controls and scan button
- KPI metrics row (upcoming earnings count, next report, days until)
- Interactive earnings calendar table with clickable tickers

**Ticker Deep-Dive (`/ticker/AAPL`)**
- Company header with sentiment badge (Bullish / Bearish / Neutral)
- Metrics row: EPS estimate, revenue estimate, sentiment score, avg earnings move
- **Sentiment tab** — Donut chart + bar chart showing bullish/bearish/neutral distribution, sample social posts
- **Historical tab** — Grouped bar chart (EPS surprise % vs next-day move %), data table, summary stats
- **News tab** — Styled headline cards with links, source, publication date
- **AI Brief tab** — Generate a Claude-powered pre-earnings brief with one click, download as Markdown

## Architecture

```
src/earnings_brief/
├── web.py                 # Flask web application (API + page routes)
├── templates/
│   ├── base.html          # Dark-themed base layout with nav
│   ├── dashboard.html     # Earnings calendar dashboard
│   └── ticker.html        # Ticker deep-dive with tabs
├── static/
│   ├── css/style.css      # Glass-morphism, animations, custom dark theme
│   └── js/
│       ├── dashboard.js   # Calendar scanning and display logic
│       └── ticker.js      # Research rendering, charts, brief generation
├── app.py                 # Streamlit dashboard (alternative UI)
├── cli.py                 # Rich CLI interface (scan / brief / calendar)
├── orchestrator.py        # Main pipeline — wires all modules together
├── earnings_calendar.py   # Fetches upcoming earnings dates via yfinance
├── news_scraper.py        # Scrapes headlines from Google/Yahoo RSS, Finviz, NewsAPI
├── sentiment.py           # Social sentiment from Reddit & StockTwits
├── historical.py          # Historical earnings reactions & post-earnings moves
├── brief_generator.py     # Claude-powered brief generation
└── models.py              # Shared dataclasses
```

## Quick Start — macOS

### 1. Prerequisites

Install Python 3.10+ via [Homebrew](https://brew.sh):

```bash
# Install Homebrew (skip if you already have it)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.12
```

### 2. Clone & Install

```bash
git clone https://github.com/powoso/claude-Earnings-Calendar-Sentiment-Analyzer-.git
cd claude-Earnings-Calendar-Sentiment-Analyzer-

# Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install the package
pip install -e .
```

### 3. Set Your API Key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or copy the example env file and fill in your keys:

```bash
cp .env.example .env
# Edit .env with your favorite editor
```

### 4. Launch the Web App

```bash
# Option A: Flask web app (recommended — beautiful dark theme)
earnings-brief-web
# → Opens at http://localhost:5000

# Option B: Streamlit dashboard (alternative)
streamlit run src/earnings_brief/app.py
# → Opens at http://localhost:8501
```

### 5. Or Use the CLI

```bash
# Generate a brief for a single ticker
earnings-brief brief AAPL

# Scan the default watchlist for upcoming earnings
earnings-brief scan

# Scan specific tickers, looking 30 days ahead
earnings-brief scan --days 30 AAPL MSFT NVDA GOOGL

# Just show the earnings calendar
earnings-brief calendar
```

## Quick Start — Linux / Windows

```bash
# Ensure Python 3.10+ is installed
python3 --version

# Clone and install
git clone https://github.com/powoso/claude-Earnings-Calendar-Sentiment-Analyzer-.git
cd claude-Earnings-Calendar-Sentiment-Analyzer-
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .

# Set API key
export ANTHROPIC_API_KEY="sk-ant-..."  # On Windows: set ANTHROPIC_API_KEY=sk-ant-...

# Run the web app
earnings-brief-web
# → http://localhost:5000
```

## Three Interfaces

| Interface | Command | URL | Best For |
|-----------|---------|-----|----------|
| **Web App** | `earnings-brief-web` | `http://localhost:5000` | Full visual experience with charts |
| **Streamlit** | `streamlit run src/earnings_brief/app.py` | `http://localhost:8501` | Quick data exploration |
| **CLI** | `earnings-brief brief AAPL` | Terminal | Automation and scripting |

## CLI Commands

| Command                  | Description                                            |
|--------------------------|--------------------------------------------------------|
| `brief <TICKER>`        | Generate a full pre-earnings brief for one ticker      |
| `scan [TICKERS...]`     | Find upcoming earnings and generate briefs for each    |
| `calendar [TICKERS...]` | Display a table of upcoming earnings dates             |

### CLI Options

| Flag             | Description                                       |
|------------------|---------------------------------------------------|
| `--days N`       | Look-ahead window in days (default: 14)           |
| `--model MODEL`  | Claude model to use (default: `claude-sonnet-4-6`) |
| `-o FILE`        | Save briefs to a markdown file                    |
| `-v`             | Verbose / debug logging                           |

## What's in a Brief?

Each brief contains:

1. **Expected Move** — Estimated post-earnings price move based on historical patterns
2. **Analyst Consensus** — EPS/revenue estimates, recent rating changes, price targets
3. **Key Risks** — Top 3-5 upside and downside risks heading into the report
4. **Historical Earnings Reactions** — Past beat/miss patterns and average moves
5. **Sentiment Summary** — Current social and news sentiment
6. **Bottom Line** — A 2-3 sentence actionable summary

## Data Sources

| Data                     | Source                                                   |
|--------------------------|----------------------------------------------------------|
| Earnings dates & estimates | Yahoo Finance (yfinance)                              |
| News headlines           | Google News RSS, Yahoo Finance RSS, Finviz, NewsAPI      |
| Social sentiment         | Reddit (PRAW or JSON fallback), StockTwits               |
| Historical reactions     | Yahoo Finance earnings history + price data              |
| Brief generation         | Claude API (Anthropic)                                   |

## Optional API Keys

Set these in your environment for richer data:

```bash
# Reddit API — improves sentiment analysis with authenticated access
export REDDIT_CLIENT_ID="..."
export REDDIT_CLIENT_SECRET="..."

# NewsAPI — additional news source coverage
export NEWSAPI_KEY="..."
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run Flask in debug mode
FLASK_DEBUG=1 earnings-brief-web
```

## License

MIT
