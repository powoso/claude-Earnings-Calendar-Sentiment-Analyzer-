"""Flask web application for the Earnings Brief dashboard."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict
from datetime import date, datetime, timezone

from flask import Flask, jsonify, render_template, request

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "earnings-brief-dev-key")

    # ---- Page routes ----

    @app.route("/")
    def dashboard():
        return render_template("dashboard.html")

    @app.route("/ticker/<symbol>")
    def ticker_page(symbol: str):
        return render_template("ticker.html", ticker=symbol.upper())

    # ---- API routes ----

    @app.route("/api/calendar")
    def api_calendar():
        from earnings_brief.earnings_calendar import get_upcoming_earnings

        days = request.args.get("days", 14, type=int)
        raw_tickers = request.args.get("tickers", "")
        tickers = [t.strip().upper() for t in raw_tickers.split(",") if t.strip()] or None

        try:
            events = get_upcoming_earnings(tickers=tickers, days_ahead=days)
            return jsonify([_serialize_event(e) for e in events])
        except Exception as exc:
            logger.exception("Calendar fetch failed")
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/research/<symbol>")
    def api_research(symbol: str):
        from earnings_brief.orchestrator import _get_or_build_event, research_ticker

        try:
            event = _get_or_build_event(symbol.upper())
            research = research_ticker(event)
            return jsonify(_serialize_research(research))
        except Exception as exc:
            logger.exception("Research failed for %s", symbol)
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/brief/<symbol>", methods=["POST"])
    def api_brief(symbol: str):
        from earnings_brief.brief_generator import generate_brief
        from earnings_brief.orchestrator import _get_or_build_event, research_ticker

        try:
            event = _get_or_build_event(symbol.upper())
            research = research_ticker(event)
            brief = generate_brief(research)
            return jsonify(_serialize_brief(brief))
        except Exception as exc:
            logger.exception("Brief generation failed for %s", symbol)
            return jsonify({"error": str(exc)}), 500

    return app


# ---------------------------------------------------------------------------
# Serializers — convert dataclasses to JSON-safe dicts
# ---------------------------------------------------------------------------

def _serialize_event(event) -> dict:
    return {
        "ticker": event.ticker,
        "company_name": event.company_name,
        "earnings_date": event.earnings_date.isoformat(),
        "time_of_day": event.time_of_day,
        "eps_estimate": event.eps_estimate,
        "revenue_estimate": event.revenue_estimate,
    }


def _serialize_research(research) -> dict:
    event = research.event
    sentiment = research.sentiment
    return {
        "event": _serialize_event(event),
        "headlines": [
            {
                "title": h.title,
                "source": h.source,
                "url": h.url,
                "published": h.published.isoformat() if h.published else None,
                "snippet": h.snippet,
            }
            for h in research.headlines
        ],
        "sentiment": {
            "ticker": sentiment.ticker,
            "overall_score": sentiment.overall_score,
            "bullish_count": sentiment.bullish_count,
            "bearish_count": sentiment.bearish_count,
            "neutral_count": sentiment.neutral_count,
            "sample_posts": sentiment.sample_posts[:10],
            "sources": sentiment.sources,
        } if sentiment else None,
        "historical_reactions": [
            {
                "quarter": r.quarter,
                "report_date": r.report_date.isoformat() if r.report_date else None,
                "eps_actual": r.eps_actual,
                "eps_estimate": r.eps_estimate,
                "surprise_pct": r.surprise_pct,
                "next_day_move_pct": r.next_day_move_pct,
            }
            for r in research.historical_reactions
        ],
    }


def _serialize_brief(brief) -> dict:
    return {
        "ticker": brief.ticker,
        "company_name": brief.company_name,
        "earnings_date": brief.earnings_date.isoformat(),
        "expected_move": brief.expected_move,
        "analyst_consensus": brief.analyst_consensus,
        "key_risks": brief.key_risks,
        "historical_reactions_summary": brief.historical_reactions_summary,
        "sentiment_summary": brief.sentiment_summary,
        "full_brief": brief.full_brief,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    port = int(os.environ.get("PORT", 5000))
    app = create_app()
    print(f"\n  Earnings Brief Dashboard running at http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", "0") == "1")


if __name__ == "__main__":
    main()
