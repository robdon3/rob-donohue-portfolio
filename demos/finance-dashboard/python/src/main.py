"""
CLI entrypoint — Personal Finance Dashboard demo.

Usage:
  python -m src.main --demo
  python -m src.main --provider mock --symbols AAPL,MSFT
  FINANCE_PROVIDER=yfinance python -m src.main --demo

Extension tips:
  - Point FINANCE_PROVIDER at a new adapter registered in clients/factory.py
  - Edit config/settings.yaml for holdings / projection assumptions
  - Wire this pipeline into Streamlit or FastAPI without changing analytics
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .analytics.portfolio import PortfolioAnalytics
from .clients.factory import get_market_client
from .config_loader import (
    env_log_level,
    env_provider,
    load_env,
    load_yaml_settings,
    portfolio_from_settings,
)
from .etl.pipeline import FinanceETLPipeline
from .utils.logging_setup import get_logger, setup_logging

console = Console()
logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Personal Finance Dashboard — API-connected Python demo",
    )
    p.add_argument(
        "--provider",
        default=None,
        help="mock | yfinance | alpha_vantage (default: env FINANCE_PROVIDER or mock)",
    )
    p.add_argument(
        "--symbols",
        default=None,
        help="Comma-separated symbols override (quotes only mode)",
    )
    p.add_argument(
        "--demo",
        action="store_true",
        help="Run full portfolio demo from config/settings.yaml",
    )
    p.add_argument(
        "--history-days",
        type=int,
        default=None,
        help="Override history window",
    )
    p.add_argument(
        "--export-json",
        type=Path,
        default=None,
        help="Optional path to write snapshot JSON",
    )
    p.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Optional directory for CSV artifacts",
    )
    return p


def print_positions(positions) -> None:
    table = Table(title="Positions")
    for col in ("symbol", "shares", "price", "market_value", "unrealized_pnl", "weight_pct"):
        table.add_column(col)
    if positions is None or positions.empty:
        console.print("[yellow]No positions[/yellow]")
        return
    for _, r in positions.iterrows():
        pnl = r.get("unrealized_pnl")
        pnl_s = f"{pnl:,.2f}" if pnl is not None else "—"
        price = r.get("price")
        mv = r.get("market_value")
        table.add_row(
            str(r["symbol"]),
            f"{r['shares']:g}",
            f"{price:,.2f}" if price is not None else "—",
            f"{mv:,.2f}" if mv is not None else "—",
            pnl_s,
            f"{r.get('weight_pct', 0):.1f}%",
        )
    console.print(table)


def run_demo(args: argparse.Namespace) -> int:
    settings = load_yaml_settings()
    name, cash, holdings = portfolio_from_settings(settings)
    market_cfg = settings.get("market", {})
    analytics_cfg = settings.get("analytics", {})
    history_days = args.history_days or int(market_cfg.get("history_days", 90))

    provider = args.provider or env_provider()
    client = get_market_client(provider)
    cache = args.cache_dir or (Path(__file__).resolve().parent.parent / "data" / "output")
    pipeline = FinanceETLPipeline(client, cache_dir=cache)

    # Optional symbol override: replace holdings weights equally (demo convenience)
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
        from .models.domain import Holding

        holdings = [
            Holding(symbol=s, shares=10, cost_basis=100.0) for s in symbols
        ]

    result = pipeline.run_portfolio_etl(
        holdings=holdings,
        history_days=history_days,
    )

    analytics = PortfolioAnalytics(
        expected_annual_return=float(analytics_cfg.get("expected_annual_return", 0.07)),
        projection_years=int(analytics_cfg.get("projection_years", 10)),
        risk_free_rate=float(analytics_cfg.get("risk_free_rate", 0.04)),
    )
    snap = analytics.snapshot(name, result["positions"], cash)
    allocation = analytics.allocation_table(result["positions"], cash)
    projection = analytics.project_growth(snap.total_market_value)
    metrics = analytics.summary_metrics(result["history"])

    console.rule(f"[bold]{snap.name}[/bold]")
    console.print(
        f"Provider: [cyan]{result['provider']}[/cyan]  |  "
        f"As of: {snap.as_of.isoformat()}  |  "
        f"Total MV: [green]${snap.total_market_value:,.2f}[/green]  |  "
        f"Unrealized P&L: ${snap.unrealized_pnl:,.2f} ({snap.unrealized_pnl_pct:.2f}%)"
    )
    print_positions(result["positions"])

    alloc_table = Table(title="Allocation (incl. cash)")
    alloc_table.add_column("asset")
    alloc_table.add_column("market_value")
    alloc_table.add_column("weight_pct")
    for _, r in allocation.iterrows():
        alloc_table.add_row(
            str(r["asset"]),
            f"${r['market_value']:,.2f}",
            f"{r['weight_pct']:.1f}%",
        )
    console.print(alloc_table)

    if metrics:
        console.print(f"History metrics ({result['primary_symbol']}): {metrics}")

    console.print(
        f"Projection (year {int(projection.iloc[-1]['year'])}): "
        f"${float(projection.iloc[-1]['value']):,.2f} "
        f"@ assumed {analytics.expected_annual_return:.1%} annual"
    )

    if args.export_json:
        payload = {
            "snapshot": snap.model_dump(mode="json"),
            "metrics": metrics,
            "projection": projection.to_dict(orient="records"),
            "provider": result["provider"],
        }
        args.export_json.parent.mkdir(parents=True, exist_ok=True)
        args.export_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        console.print(f"[green]Wrote[/green] {args.export_json}")

    console.print(
        "\n[dim]Not financial advice. Demo framework for architecture evaluation.[/dim]"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    load_env()
    setup_logging(env_log_level())
    args = build_parser().parse_args(argv)

    # Default to demo if no mode flags — friendlier for first run
    if not args.demo and not args.symbols:
        args.demo = True

    try:
        return run_demo(args)
    except Exception as exc:
        logger.exception("run failed: %s", exc)
        console.print(f"[red]Error:[/red] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
