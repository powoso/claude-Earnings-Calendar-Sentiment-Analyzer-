# Earnings Calendar Sentiment Analyzer

A web dashboard and CLI tool that pulls upcoming earnings dates, scrapes recent news headlines and social sentiment for each ticker, and uses Claude to generate a pre-earnings brief with expected move, analyst consensus, key risks, and historical earnings reactions.

## Features

- **Interactive Web Dashboard** — Streamlit-powered UI with dark theme, Plotly charts, and real-time research
- **Earnings Calendar** — Scan 30+ large-cap tickers for upcoming earnings within a configurable date range
- **Multi-Source News** — Headlines aggregated from Google News, Yahoo Finance, Finviz, and NewsAPI
- **Social Sentiment** — Bullish/bearish scoring from Reddit (r/wallstreetbets, r/stocks, r/investing) and StockTwits
- **Historical Reactions** — Past 8 quarters of EPS surprises and next-day price moves with interactive charts
- **Claude-Powered Briefs** — AI-generated pre-earnings analysis covering expected move, consensus, risks, and sentiment
- **Rich CLI** — Terminal interface with scan, brief, and calendar commands
- **Export** — Download briefs as Markdown files from the UI or CLI

## Web Dashboard

The Streamlit dashboard provides a visual interface with:

- **Earnings Calendar** — Interactive table of upcoming earnings across your watchlist
- **Ticker Deep-Dive** — Click any ticker to see:
  - Company header with earnings date and analyst estimates
  - Sentiment gauge with bullish/bearish/neutral donut chart and bar breakdown
  - Historical reactions chart (EPS surprise and next-day price move per quarter)
  - Recent news headlines feed with linked cards
  - Full Claude-generated pre-earnings brief
- **Sidebar Controls** — Ticker search, date range slider, watchlist presets (Large-Caps, Magnificent 7, FAANG+, Semiconductors, Finance, Custom)
- **Export** — Download any brief as a Markdown file

## Architecture

```
src/earnings_brief/
├── app.py                 # Streamlit web dashboard
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

### 4. Launch the Web Dashboard

```bash
streamlit run src/earnings_brief/app.py
```

Opens automatically in your browser at `http://localhost:8501`.

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

# Run the dashboard
streamlit run src/earnings_brief/app.py
```

## CLI Commands

| Command                  | Description                                            |
|--------------------------|--------------------------------------------------------|
| `brief <TICKER>`        | Generate a full pre-earnings brief for one ticker      |
| `scan [TICKERS...]`     | Find upcoming earnings and generate briefs for each    |
| `calendar [TICKERS...]` | Display a table of upcoming earnings dates             |

### Common Options

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
```

## License

MIT
