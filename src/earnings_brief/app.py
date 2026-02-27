"""Streamlit web dashboard for the Earnings Brief generator."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Page configuration — must be the first Streamlit call
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Earnings Brief Dashboard",
    page_icon="\U0001f4ca",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS for a polished, dark-themed financial dashboard
# ---------------------------------------------------------------------------

_CUSTOM_CSS = """
<style>
/* ---------- Global tweaks ---------- */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #0e1117 0%, #161b22 100%);
}

/* ---------- Header banner ---------- */
.hero-banner {
    background: linear-gradient(135deg, #1a1f2e 0%, #0d2137 50%, #0a1628 100%);
    border: 1px solid rgba(99, 110, 250, 0.25);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    margin-bottom: 1.5rem;
    text-align: center;
}
.hero-banner h1 {
    background: linear-gradient(90deg, #636efa, #00cc96);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.4rem;
    font-weight: 800;
    margin-bottom: 0.3rem;
}
.hero-banner p {
    color: #8b949e;
    font-size: 1.1rem;
}

/* ---------- Metric cards ---------- */
[data-testid="stMetric"] {
    background: rgba(22, 27, 34, 0.8);
    border: 1px solid rgba(99, 110, 250, 0.15);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.25);
}
[data-testid="stMetricLabel"] {
    color: #8b949e !important;
    font-size: 0.85rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
[data-testid="stMetricValue"] {
    font-weight: 700 !important;
}

/* ---------- Section headers ---------- */
.section-header {
    color: #c9d1d9;
    font-size: 1.3rem;
    font-weight: 700;
    border-bottom: 2px solid rgba(99, 110, 250, 0.3);
    padding-bottom: 0.5rem;
    margin-top: 1.5rem;
    margin-bottom: 1rem;
}

/* ---------- Ticker chip buttons ---------- */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(99, 110, 250, 0.3);
}

/* ---------- News card ---------- */
.news-card {
    background: rgba(22, 27, 34, 0.6);
    border: 1px solid rgba(139, 148, 158, 0.15);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s ease;
}
.news-card:hover {
    border-color: rgba(99, 110, 250, 0.4);
}
.news-card a {
    color: #58a6ff !important;
    text-decoration: none;
    font-weight: 600;
    font-size: 1rem;
}
.news-card a:hover {
    text-decoration: underline;
}
.news-meta {
    color: #8b949e;
    font-size: 0.8rem;
    margin-top: 0.3rem;
}
.news-snippet {
    color: #adb5bd;
    font-size: 0.9rem;
    margin-top: 0.4rem;
}

/* ---------- Sentiment badge ---------- */
.sentiment-badge {
    display: inline-block;
    padding: 0.3rem 0.9rem;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.9rem;
    letter-spacing: 0.03em;
}
.sentiment-bullish {
    background: rgba(0, 204, 150, 0.15);
    color: #00cc96;
    border: 1px solid rgba(0, 204, 150, 0.3);
}
.sentiment-bearish {
    background: rgba(239, 85, 59, 0.15);
    color: #ef553b;
    border: 1px solid rgba(239, 85, 59, 0.3);
}
.sentiment-neutral {
    background: rgba(139, 148, 158, 0.15);
    color: #8b949e;
    border: 1px solid rgba(139, 148, 158, 0.3);
}

/* ---------- Tabs styling ---------- */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 0.6rem 1.5rem;
    font-weight: 600;
}

/* ---------- Dataframe ---------- */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
    border-right: 1px solid rgba(99, 110, 250, 0.15);
}
</style>
"""

st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def _init_state() -> None:
    defaults: dict = {
        "calendar_events": None,
        "selected_ticker": None,
        "selected_event": None,
        "research_cache": {},
        "brief_cache": {},
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

_WATCHLIST_PRESETS: dict[str, list[str] | None] = {
    "Top 30 Large-Caps": None,  # None → uses DEFAULT_WATCHLIST
    "Magnificent 7": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"],
    "FAANG+": ["AAPL", "AMZN", "META", "GOOGL", "NFLX", "MSFT", "NVDA", "TSLA"],
    "Semiconductors": ["NVDA", "AMD", "INTC", "AVGO", "QCOM", "MU", "AMAT", "LRCX"],
    "Finance": ["JPM", "GS", "MS", "BAC", "WFC", "C", "BLK", "SCHW"],
    "Custom": [],
}


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            "<h1 style='background: linear-gradient(90deg, #636efa, #00cc96); "
            "-webkit-background-clip: text; -webkit-text-fill-color: transparent; "
            "font-size: 1.6rem; margin-bottom: 0;'>"
            "\U0001f4ca Earnings Brief</h1>",
            unsafe_allow_html=True,
        )
        st.caption("Pre-earnings analysis powered by Claude")
        st.divider()

        # --- Direct ticker lookup ---
        st.markdown("##### \U0001f50d Analyze a Ticker")
        ticker_input = st.text_input(
            "Ticker symbol",
            placeholder="e.g. AAPL",
            label_visibility="collapsed",
        )
        if ticker_input and st.button("Analyze", type="primary", use_container_width=True):
            st.session_state["selected_ticker"] = ticker_input.strip().upper()
            st.session_state["selected_event"] = None
            st.rerun()

        st.divider()

        # --- Calendar controls ---
        st.markdown("##### \U0001f4c5 Earnings Calendar")
        days_ahead = st.slider("Days ahead", min_value=1, max_value=90, value=14)

        preset = st.selectbox("Watchlist", list(_WATCHLIST_PRESETS.keys()))
        custom_tickers: list[str] | None = _WATCHLIST_PRESETS.get(preset)

        if preset == "Custom":
            raw = st.text_area(
                "Tickers (comma-separated)",
                placeholder="AAPL, MSFT, NVDA, GOOGL",
            )
            custom_tickers = (
                [t.strip().upper() for t in raw.split(",") if t.strip()] if raw else None
            )

        if st.button("Scan Calendar", type="primary", use_container_width=True):
            from earnings_brief.earnings_calendar import get_upcoming_earnings

            with st.spinner("Fetching earnings dates\u2026"):
                events = get_upcoming_earnings(tickers=custom_tickers, days_ahead=days_ahead)
            st.session_state["calendar_events"] = events
            st.session_state["selected_ticker"] = None
            st.session_state["selected_event"] = None
            st.rerun()

        st.divider()
        st.caption("Requires `ANTHROPIC_API_KEY` for brief generation")


# ---------------------------------------------------------------------------
# Calendar (dashboard) view
# ---------------------------------------------------------------------------

def _render_calendar() -> None:
    # Hero banner
    st.markdown(
        '<div class="hero-banner">'
        "<h1>Earnings Brief Dashboard</h1>"
        "<p>Scan upcoming earnings \u00b7 Research sentiment &amp; history \u00b7 Generate Claude-powered briefs</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    events = st.session_state["calendar_events"]

    if events is None:
        st.info(
            "\U0001f449 Click **Scan Calendar** in the sidebar to load upcoming earnings, "
            "or type a ticker and hit **Analyze** for a direct deep-dive."
        )
        return

    if not events:
        st.warning(
            "No upcoming earnings found in the specified window. "
            "Try increasing the **Days ahead** slider or using a different watchlist."
        )
        return

    # KPI row
    next_event = events[0]
    days_until = (next_event.earnings_date - date.today()).days
    c1, c2, c3 = st.columns(3)
    c1.metric("Upcoming Earnings", len(events))
    c2.metric("Next Report", f"{next_event.ticker} \u2014 {next_event.earnings_date.isoformat()}")
    c3.metric("Days Until Next", days_until)

    st.markdown('<div class="section-header">Earnings Calendar</div>', unsafe_allow_html=True)

    # Build DataFrame
    rows = []
    for e in events:
        rows.append({
            "Date": e.earnings_date.isoformat(),
            "Ticker": e.ticker,
            "Company": e.company_name,
            "EPS Est.": f"${e.eps_estimate:.2f}" if e.eps_estimate is not None else "\u2014",
            "Rev Est.": _fmt_revenue(e.revenue_estimate) if e.revenue_estimate is not None else "\u2014",
            "Timing": e.time_of_day.replace("_", " ").title(),
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True, height=min(len(rows) * 38 + 38, 600))

    # Quick-analyze ticker buttons
    st.markdown('<div class="section-header">Quick Analyze</div>', unsafe_allow_html=True)
    cols_per_row = 8
    for row_start in range(0, len(events), cols_per_row):
        chunk = events[row_start : row_start + cols_per_row]
        cols = st.columns(cols_per_row)
        for i, event in enumerate(chunk):
            with cols[i]:
                if st.button(event.ticker, key=f"cal_{event.ticker}", use_container_width=True):
                    st.session_state["selected_ticker"] = event.ticker
                    st.session_state["selected_event"] = event
                    st.rerun()


# ---------------------------------------------------------------------------
# Deep-dive view
# ---------------------------------------------------------------------------

def _render_deep_dive(ticker: str) -> None:
    from earnings_brief.brief_generator import generate_brief
    from earnings_brief.orchestrator import _get_or_build_event, research_ticker

    # Back button
    if st.button("\u2190 Back to Calendar"):
        st.session_state["selected_ticker"] = None
        st.session_state["selected_event"] = None
        st.rerun()

    # Fetch or reuse research
    research = st.session_state["research_cache"].get(ticker)
    if research is None:
        with st.status(f"Researching {ticker}\u2026", expanded=True) as status:
            st.write("Fetching earnings data\u2026")
            event = st.session_state.get("selected_event") or _get_or_build_event(ticker)
            st.write("Scraping news headlines\u2026")
            st.write("Gathering social sentiment\u2026")
            st.write("Loading historical reactions\u2026")
            research = research_ticker(event)
            st.session_state["research_cache"][ticker] = research
            status.update(label=f"Research complete for {ticker}", state="complete")

    event = research.event

    # Company header
    st.markdown(
        f"<div class='hero-banner' style='text-align:left; padding: 1.5rem 2rem;'>"
        f"<h1 style='font-size:2rem;'>{event.ticker}</h1>"
        f"<p style='font-size:1.2rem; color:#c9d1d9;'>{event.company_name}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Metrics row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Earnings Date", event.earnings_date.isoformat())
    c2.metric(
        "EPS Estimate",
        f"${event.eps_estimate:.2f}" if event.eps_estimate is not None else "N/A",
    )
    c3.metric(
        "Revenue Estimate",
        _fmt_revenue(event.revenue_estimate) if event.revenue_estimate is not None else "N/A",
    )
    sentiment = research.sentiment
    if sentiment and sentiment.sources:
        score = sentiment.overall_score
        label = "Bullish" if score > 0.1 else ("Bearish" if score < -0.1 else "Neutral")
        c4.metric(
            "Sentiment",
            f"{score:+.2f}",
            delta=label,
            delta_color="normal" if score > 0.1 else ("inverse" if score < -0.1 else "off"),
        )
    else:
        c4.metric("Sentiment", "N/A")

    # Tabs
    tab_sentiment, tab_historical, tab_news, tab_brief = st.tabs(
        ["\U0001f4ca Sentiment", "\U0001f4c8 Historical Reactions", "\U0001f4f0 News", "\U0001f4dd Full Brief"]
    )

    with tab_sentiment:
        _render_sentiment(research.sentiment)

    with tab_historical:
        _render_historical(research.historical_reactions)

    with tab_news:
        _render_news(research.headlines)

    with tab_brief:
        _render_brief_tab(ticker, research)


# ---------------------------------------------------------------------------
# Tab: Sentiment
# ---------------------------------------------------------------------------

def _render_sentiment(sentiment) -> None:
    if sentiment is None or not sentiment.sources:
        st.info("No sentiment data available. Configure Reddit or StockTwits API keys for richer data.")
        return

    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    score = sentiment.overall_score
    badge_cls = "sentiment-bullish" if score > 0.1 else ("sentiment-bearish" if score < -0.1 else "sentiment-neutral")
    badge_text = "BULLISH" if score > 0.1 else ("BEARISH" if score < -0.1 else "NEUTRAL")

    with c1:
        st.metric("Overall Score", f"{score:+.3f}")
        st.markdown(f'<span class="sentiment-badge {badge_cls}">{badge_text}</span>', unsafe_allow_html=True)
    c2.metric("\U0001f7e2 Bullish", sentiment.bullish_count)
    c3.metric("\U0001f534 Bearish", sentiment.bearish_count)
    c4.metric("\u26aa Neutral", sentiment.neutral_count)

    st.markdown("")

    # Plotly donut + bar
    col_left, col_right = st.columns(2)

    with col_left:
        fig = go.Figure(data=[go.Pie(
            labels=["Bullish", "Bearish", "Neutral"],
            values=[sentiment.bullish_count, sentiment.bearish_count, sentiment.neutral_count],
            hole=0.55,
            marker=dict(colors=["#00cc96", "#ef553b", "#636efa"]),
            textinfo="label+percent",
            textfont=dict(size=13),
        )])
        fig.update_layout(
            title=dict(text="Sentiment Distribution", font=dict(size=16)),
            template="plotly_dark",
            height=350,
            margin=dict(t=50, b=20, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        fig = go.Figure(data=[go.Bar(
            x=["Bullish", "Bearish", "Neutral"],
            y=[sentiment.bullish_count, sentiment.bearish_count, sentiment.neutral_count],
            marker_color=["#00cc96", "#ef553b", "#636efa"],
            text=[sentiment.bullish_count, sentiment.bearish_count, sentiment.neutral_count],
            textposition="auto",
        )])
        fig.update_layout(
            title=dict(text="Post Counts", font=dict(size=16)),
            yaxis_title="Posts",
            template="plotly_dark",
            height=350,
            margin=dict(t=50, b=20, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.caption(f"Sources: {', '.join(sentiment.sources)}")

    # Sample posts
    if sentiment.sample_posts:
        with st.expander("Sample Social Posts", expanded=False):
            for post in sentiment.sample_posts[:8]:
                st.text(post[:300])
                st.divider()


# ---------------------------------------------------------------------------
# Tab: Historical Reactions
# ---------------------------------------------------------------------------

def _render_historical(reactions: list) -> None:
    if not reactions:
        st.info("No historical earnings reaction data available for this ticker.")
        return

    quarters = [r.quarter for r in reversed(reactions)]
    surprises = [r.surprise_pct if r.surprise_pct is not None else 0 for r in reversed(reactions)]
    moves = [r.next_day_move_pct if r.next_day_move_pct is not None else 0 for r in reversed(reactions)]
    move_colors = ["#00cc96" if m >= 0 else "#ef553b" for m in moves]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="EPS Surprise %",
        x=quarters,
        y=surprises,
        marker_color="#636efa",
        opacity=0.85,
    ))
    fig.add_trace(go.Bar(
        name="Next-Day Move %",
        x=quarters,
        y=moves,
        marker_color=move_colors,
        opacity=0.85,
    ))
    fig.update_layout(
        title=dict(text="Earnings Reactions by Quarter", font=dict(size=18)),
        barmode="group",
        yaxis_title="Percentage (%)",
        template="plotly_dark",
        height=420,
        margin=dict(t=60, b=40, l=40, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.add_hline(y=0, line_dash="dot", line_color="rgba(139,148,158,0.4)")
    st.plotly_chart(fig, use_container_width=True)

    # Data table
    rows = []
    for r in reactions:
        rows.append({
            "Quarter": r.quarter,
            "EPS Est.": f"${r.eps_estimate:.2f}" if r.eps_estimate is not None else "\u2014",
            "EPS Actual": f"${r.eps_actual:.2f}" if r.eps_actual is not None else "\u2014",
            "Surprise %": f"{r.surprise_pct:+.1f}%" if r.surprise_pct is not None else "\u2014",
            "Next-Day Move": f"{r.next_day_move_pct:+.1f}%" if r.next_day_move_pct is not None else "\u2014",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Summary stats
    valid_moves = [r.next_day_move_pct for r in reactions if r.next_day_move_pct is not None]
    if valid_moves:
        avg_move = sum(abs(m) for m in valid_moves) / len(valid_moves)
        beats = sum(1 for r in reactions if r.surprise_pct is not None and r.surprise_pct > 0)
        total = sum(1 for r in reactions if r.surprise_pct is not None)
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Avg Absolute Move", f"{avg_move:.1f}%")
        sc2.metric("Beat Rate", f"{beats}/{total}" if total else "\u2014")
        sc3.metric("Last Move", f"{valid_moves[0]:+.1f}%" if valid_moves else "\u2014")


# ---------------------------------------------------------------------------
# Tab: News
# ---------------------------------------------------------------------------

def _render_news(headlines: list) -> None:
    if not headlines:
        st.info("No recent news headlines found for this ticker.")
        return

    for h in headlines:
        pub_str = h.published.strftime("%b %d, %Y %H:%M UTC") if h.published else ""
        card_html = (
            f'<div class="news-card">'
            f'<a href="{h.url}" target="_blank">{_escape_html(h.title)}</a>'
            f'<div class="news-meta">{_escape_html(h.source)}'
            f'{" &middot; " + pub_str if pub_str else ""}</div>'
        )
        if h.snippet:
            card_html += f'<div class="news-snippet">{_escape_html(h.snippet[:250])}</div>'
        card_html += "</div>"
        st.markdown(card_html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Tab: Full Brief
# ---------------------------------------------------------------------------

def _render_brief_tab(ticker: str, research) -> None:
    from earnings_brief.brief_generator import generate_brief

    brief = st.session_state["brief_cache"].get(ticker)

    if brief is None:
        st.markdown(
            '<div class="hero-banner" style="padding: 2rem;">'
            "<h1 style='font-size:1.5rem;'>Generate Pre-Earnings Brief</h1>"
            "<p>Click below to have Claude analyze all research data and produce a comprehensive brief.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        if st.button(
            "\U0001f680 Generate Brief with Claude",
            type="primary",
            use_container_width=True,
            key=f"gen_{ticker}",
        ):
            try:
                with st.spinner("Claude is analyzing the data\u2026 This may take 15\u201330 seconds."):
                    brief = generate_brief(research)
                    st.session_state["brief_cache"][ticker] = brief
                st.rerun()
            except Exception as e:
                st.error(f"Failed to generate brief: {e}")
                st.info("Make sure `ANTHROPIC_API_KEY` is set in your environment.")
        return

    # Render the full brief
    st.markdown(brief.full_brief)
    st.divider()

    # Export
    col_dl, col_regen, _ = st.columns([1, 1, 3])
    md_content = (
        f"# {brief.ticker} \u2014 {brief.company_name}\n\n"
        f"**Earnings Date:** {brief.earnings_date.isoformat()}\n\n"
        f"{brief.full_brief}"
    )
    with col_dl:
        st.download_button(
            label="\U0001f4e5 Download as Markdown",
            data=md_content,
            file_name=f"{ticker}_earnings_brief.md",
            mime="text/markdown",
        )
    with col_regen:
        if st.button("\U0001f504 Regenerate", key=f"regen_{ticker}"):
            try:
                with st.spinner("Regenerating\u2026"):
                    brief = generate_brief(research)
                    st.session_state["brief_cache"][ticker] = brief
                st.rerun()
            except Exception as e:
                st.error(f"Regeneration failed: {e}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_revenue(val: float | None) -> str:
    if val is None:
        return "N/A"
    if abs(val) >= 1e9:
        return f"${val / 1e9:.2f}B"
    if abs(val) >= 1e6:
        return f"${val / 1e6:.1f}M"
    return f"${val:,.0f}"


def _escape_html(text: str) -> str:
    """Minimal HTML escaping for user-supplied text rendered in HTML blocks."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    _init_state()
    _render_sidebar()

    if st.session_state["selected_ticker"]:
        _render_deep_dive(st.session_state["selected_ticker"])
    else:
        _render_calendar()


if __name__ == "__main__":
    main()
