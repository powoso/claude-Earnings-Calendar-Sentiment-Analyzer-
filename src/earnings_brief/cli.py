"""Rich CLI for the Earnings Brief generator."""

from __future__ import annotations

import argparse
import logging
import os
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    _configure_logging(args.verbose)

    # Lazy imports so --help is instant.
    from earnings_brief.models import EarningsBrief

    if args.command == "scan":
        _cmd_scan(args)
    elif args.command == "brief":
        _cmd_brief(args)
    elif args.command == "calendar":
        _cmd_calendar(args)
    else:
        console.print("[red]Unknown command. Use --help for usage.[/red]")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def _cmd_scan(args: argparse.Namespace) -> None:
    """Scan upcoming earnings and generate briefs for all of them."""
    from earnings_brief.orchestrator import run_pipeline

    tickers = args.tickers if args.tickers else None

    console.print(Panel.fit(
        "[bold cyan]Earnings Brief Scanner[/bold cyan]\n"
        f"Looking ahead {args.days} days",
        border_style="cyan",
    ))

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task("Scanning upcoming earnings & generating briefs…", total=None)
        briefs = run_pipeline(
            tickers=tickers,
            days_ahead=args.days,
            model=args.model,
        )
        progress.update(task, completed=True)

    if not briefs:
        console.print("[yellow]No upcoming earnings found in the specified window.[/yellow]")
        return

    for brief in briefs:
        _render_brief(brief)

    if args.output:
        _save_briefs(briefs, args.output)


def _cmd_brief(args: argparse.Namespace) -> None:
    """Generate a brief for a single ticker."""
    from earnings_brief.orchestrator import run_single

    ticker = args.ticker.upper()
    console.print(Panel.fit(
        f"[bold cyan]Generating Pre-Earnings Brief[/bold cyan]\n"
        f"Ticker: [bold]{ticker}[/bold]",
        border_style="cyan",
    ))

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        task_id = progress.add_task(f"Researching {ticker}…", total=None)
        brief = run_single(ticker, model=args.model)
        progress.update(task_id, completed=True)

    _render_brief(brief)

    if args.output:
        _save_briefs([brief], args.output)


def _cmd_calendar(args: argparse.Namespace) -> None:
    """Display the upcoming earnings calendar."""
    from earnings_brief.earnings_calendar import get_upcoming_earnings

    tickers = args.tickers if args.tickers else None

    console.print(Panel.fit(
        "[bold cyan]Upcoming Earnings Calendar[/bold cyan]\n"
        f"Next {args.days} days",
        border_style="cyan",
    ))

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task("Fetching earnings dates…", total=None)
        events = get_upcoming_earnings(tickers=tickers, days_ahead=args.days)
        progress.update(task, completed=True)

    if not events:
        console.print("[yellow]No upcoming earnings found.[/yellow]")
        return

    table = Table(title="Upcoming Earnings", show_lines=True)
    table.add_column("Date", style="cyan", no_wrap=True)
    table.add_column("Ticker", style="bold green")
    table.add_column("Company", style="white")
    table.add_column("EPS Est.", justify="right")
    table.add_column("Rev Est.", justify="right")

    for e in events:
        eps = f"${e.eps_estimate:.2f}" if e.eps_estimate is not None else "-"
        rev = _fmt_revenue(e.revenue_estimate) if e.revenue_estimate is not None else "-"
        table.add_row(
            e.earnings_date.isoformat(),
            e.ticker,
            e.company_name,
            eps,
            rev,
        )

    console.print(table)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _render_brief(brief) -> None:
    """Render a single EarningsBrief to the console."""
    header = (
        f"[bold green]{brief.ticker}[/bold green] — "
        f"{brief.company_name}\n"
        f"Earnings Date: [cyan]{brief.earnings_date.isoformat()}[/cyan]"
    )
    console.print()
    console.print(Panel(header, border_style="green", expand=False))
    console.print(Markdown(brief.full_brief))
    console.print()
    console.rule(style="dim")


def _save_briefs(briefs: list, output_path: str) -> None:
    """Write briefs to a markdown file."""
    with open(output_path, "w") as f:
        for brief in briefs:
            f.write(f"# {brief.ticker} — {brief.company_name}\n\n")
            f.write(f"**Earnings Date:** {brief.earnings_date.isoformat()}\n\n")
            f.write(brief.full_brief)
            f.write("\n\n---\n\n")
    console.print(f"[green]Briefs saved to {output_path}[/green]")


# ---------------------------------------------------------------------------
# Arg parsing
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="earnings-brief",
        description="Pre-earnings brief generator powered by Claude.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--model", default=None, help="Claude model to use (default: claude-sonnet-4-6)")
    parser.add_argument("-o", "--output", default=None, help="Save briefs to a markdown file")

    sub = parser.add_subparsers(dest="command")

    # scan
    scan_p = sub.add_parser("scan", help="Scan upcoming earnings and generate briefs")
    scan_p.add_argument("--days", type=int, default=14, help="Days ahead to scan (default: 14)")
    scan_p.add_argument("tickers", nargs="*", help="Optional list of tickers (default: top-30 large caps)")

    # brief
    brief_p = sub.add_parser("brief", help="Generate a brief for a single ticker")
    brief_p.add_argument("ticker", help="Stock ticker symbol (e.g. AAPL)")

    # calendar
    cal_p = sub.add_parser("calendar", help="Show the upcoming earnings calendar")
    cal_p.add_argument("--days", type=int, default=14, help="Days ahead to scan (default: 14)")
    cal_p.add_argument("tickers", nargs="*", help="Optional list of tickers")

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    return args


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _fmt_revenue(val: float) -> str:
    if abs(val) >= 1e9:
        return f"${val / 1e9:.2f}B"
    if abs(val) >= 1e6:
        return f"${val / 1e6:.1f}M"
    return f"${val:,.0f}"


if __name__ == "__main__":
    main()
