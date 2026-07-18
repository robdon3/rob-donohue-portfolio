"""
CLI entrypoint — Financial Worksheet OS + market portfolio demos.

Usage:
  python -m src.main --worksheet
  python -m src.main --worksheet --export-json data/output/worksheet.json
  python -m src.main --market-demo
  FINANCE_PROVIDER=yfinance python -m src.main --market-demo

Clean-room: --worksheet uses synthetic_household.yaml only (no real PII).
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
from .worksheet.engine import bundle_to_jsonable, run_worksheet

console = Console()
logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Financial Worksheet OS — clean-room multi-view finance demo",
    )
    p.add_argument(
        "--worksheet",
        action="store_true",
        help="Run multi-view worksheet OS (synthetic household). Default mode.",
    )
    p.add_argument(
        "--market-demo",
        action="store_true",
        help="Run original market-data portfolio demo (API adapters)",
    )
    p.add_argument(
        "--demo",
        action="store_true",
        help="Alias for --worksheet (backward compatible)",
    )
    p.add_argument(
        "--provider",
        default=None,
        help="mock | yfinance | alpha_vantage (market-demo only)",
    )
    p.add_argument(
        "--symbols",
        default=None,
        help="Comma-separated symbols override (market-demo)",
    )
    p.add_argument(
        "--history-days",
        type=int,
        default=None,
        help="Override history window (market-demo)",
    )
    p.add_argument(
        "--export-json",
        type=Path,
        default=None,
        help="Write worksheet or market snapshot JSON",
    )
    p.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Optional directory for CSV artifacts",
    )
    p.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to synthetic household YAML (worksheet mode)",
    )
    return p


def money(n: float | None) -> str:
    if n is None:
        return "—"
    return f"${n:,.2f}"


def run_worksheet_cli(args: argparse.Namespace) -> int:
    bundle = run_worksheet(config_path=args.config)
    c = bundle.cockpit

    console.rule("[bold cyan]Purpose-built finance workbook[/bold cyan] — synthetic demo")
    console.print(f"[bold]{bundle.persona_name}[/bold]")
    console.print(f"[dim]{bundle.disclaimer}[/dim]\n")

    if bundle.areas:
        areas = Table(title="Areas (each has a job)")
        areas.add_column("area")
        areas.add_column("purpose")
        for a in bundle.areas:
            areas.add_row(str(a.get("name")), str(a.get("purpose")))
        console.print(areas)

    console.print(
        f"As of [cyan]{c.as_of}[/cyan]  |  "
        f"Net worth [green]{money(c.net_worth)}[/green]  |  "
        f"Assets {money(c.assets)}  |  Investments {money(c.investments)}  |  "
        f"Liabilities [red]{money(c.liabilities)}[/red]"
    )
    console.print(
        f"A/D ratio: {c.ad_ratio}  |  "
        f"ATH {money(c.ath_net_worth)} ({c.ath_date})  |  "
        f"ATL {money(c.atl_net_worth)} ({c.atl_date})  |  "
        f"YTD Δ {money(c.ytd_net_worth_change)}  |  "
        f"Daily Δ {money(c.daily_change)}"
    )
    console.print(
        f"Ops: card today = [yellow]{bundle.ops.get('card_of_day_name')}[/yellow] "
        f"({bundle.ops.get('weekday')})  |  {bundle.ops.get('market_directive')}"
    )

    # Accounts
    acct = Table(title="Accounts ledger")
    for col in ("name", "kind", "category", "balance", "limit", "util%"):
        acct.add_column(col)
    for r in bundle.accounts:
        util = r.get("utilization_pct")
        acct.add_row(
            str(r.get("name")),
            str(r.get("kind")),
            str(r.get("category")),
            money(r.get("balance")),
            money(r.get("credit_limit")) if r.get("credit_limit") else "—",
            f"{util:.1f}%" if util is not None else "—",
        )
    console.print(acct)

    # Debt stack
    debt = Table(title="Debt stack")
    for col in ("name", "balance", "% debt", "util%", "APR", "payoff mo", "est. date"):
        debt.add_column(col)
    for d in bundle.debt_stack:
        debt.add_row(
            d.name,
            money(d.balance),
            f"{d.pct_of_debt:.1f}%",
            f"{d.utilization_pct:.1f}%" if d.utilization_pct is not None else "—",
            f"{d.apr_pct:.1f}%" if d.apr_pct is not None else "—",
            str(d.payoff_months_est) if d.payoff_months_est is not None else "—",
            str(d.payoff_date_est) if d.payoff_date_est else "—",
        )
    console.print(debt)

    # Runway
    rw = bundle.runway
    console.print(
        f"Runway: fund {money(rw.current_fund)} / target {money(rw.target_fund)} "
        f"({rw.months_covered:.1f} of {rw.months_target:.0f} mo)  |  "
        f"deficit {money(rw.deficit)}  |  catch-up {money(rw.catchup_monthly)}/mo"
    )

    # Cashflow
    cf = bundle.cashflow
    wf = Table(title=f"Paycheck waterfall ({cf.cadence} · {money(cf.paycheck_gross)})")
    wf.add_column("bucket")
    wf.add_column("fraction")
    wf.add_column("amount")
    for b in cf.waterfall:
        wf.add_row(b.name, f"{b.fraction:.0%}", money(b.amount))
    console.print(wf)

    # Holdings sample
    hold = Table(title=f"Holdings ({len(bundle.holdings)} lines)")
    for col in ("account", "asset", "ticker", "qty", "price", "value", "type"):
        hold.add_column(col)
    for r in bundle.holdings[:12]:
        hold.add_row(
            str(r.get("account_name")),
            str(r.get("asset"))[:28],
            str(r.get("ticker") or "—"),
            f"{r.get('quantity'):g}",
            money(r.get("price")),
            money(r.get("value")),
            str(r.get("asset_type")),
        )
    if len(bundle.holdings) > 12:
        hold.add_row("…", f"+{len(bundle.holdings) - 12} more", "", "", "", "", "")
    console.print(hold)

    # Journal (Apps Script pattern)
    jtab = Table(title=f"Journal (last action: {bundle.journal_action})")
    for col in ("as_of", "assets", "liabilities", "investments", "net_worth", "note"):
        jtab.add_column(col)
    for r in bundle.journal[-6:]:
        jtab.add_row(
            str(r.get("as_of")),
            money(r.get("assets")),
            money(r.get("liabilities")),
            money(r.get("investments")),
            money(r.get("net_worth")),
            str(r.get("note") or ""),
        )
    console.print(jtab)
    console.print(f"[dim]{bundle.ops.get('automation', '')}[/dim]")

    # Payments testground
    if bundle.payments_testground:
        for sc in bundle.payments_testground:
            pt = Table(title=f"Payments testground · {sc['name']} ({money(sc['total_payment'])})")
            pt.add_column("facility")
            pt.add_column("amount")
            pt.add_column("remaining")
            pt.add_column("rule")
            for a in sc.get("allocations", []):
                pt.add_row(
                    str(a.get("name")),
                    money(a.get("amount")),
                    money(a.get("remaining")),
                    str(a.get("rule")),
                )
            console.print(pt)
            console.print(
                f"  → projected total debt {money(sc.get('projected_total_debt'))}  "
                f"[dim]{sc.get('description', '')}[/dim]"
            )

    if args.export_json:
        args.export_json.parent.mkdir(parents=True, exist_ok=True)
        payload = bundle_to_jsonable(bundle)
        args.export_json.write_text(
            json.dumps(payload, indent=2, default=str), encoding="utf-8"
        )
        console.print(f"[green]Wrote[/green] {args.export_json}")

    console.print(
        "\n[dim]Synthetic data only · Not financial advice · Architecture demo[/dim]"
    )
    return 0


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


def run_market_demo(args: argparse.Namespace) -> int:
    settings = load_yaml_settings()
    name, cash, holdings = portfolio_from_settings(settings)
    market_cfg = settings.get("market", {})
    analytics_cfg = settings.get("analytics", {})
    history_days = args.history_days or int(market_cfg.get("history_days", 90))

    provider = args.provider or env_provider()
    client = get_market_client(provider)
    cache = args.cache_dir or (Path(__file__).resolve().parent.parent / "data" / "output")
    pipeline = FinanceETLPipeline(client, cache_dir=cache)

    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
        from .models.domain import Holding

        holdings = [Holding(symbol=s, shares=10, cost_basis=100.0) for s in symbols]

    result = pipeline.run_portfolio_etl(holdings=holdings, history_days=history_days)
    analytics = PortfolioAnalytics(
        expected_annual_return=float(analytics_cfg.get("expected_annual_return", 0.07)),
        projection_years=int(analytics_cfg.get("projection_years", 10)),
        risk_free_rate=float(analytics_cfg.get("risk_free_rate", 0.04)),
    )
    snap = analytics.snapshot(name, result["positions"], cash)
    allocation = analytics.allocation_table(result["positions"], cash)
    projection = analytics.project_growth(snap.total_market_value)
    metrics = analytics.summary_metrics(result["history"])

    console.rule(f"[bold]{snap.name}[/bold] (market-demo)")
    console.print(
        f"Provider: [cyan]{result['provider']}[/cyan]  |  "
        f"Total MV: [green]{money(snap.total_market_value)}[/green]  |  "
        f"Unrealized P&L: {money(snap.unrealized_pnl)} ({snap.unrealized_pnl_pct:.2f}%)"
    )
    print_positions(result["positions"])

    alloc_table = Table(title="Allocation (incl. cash)")
    alloc_table.add_column("asset")
    alloc_table.add_column("market_value")
    alloc_table.add_column("weight_pct")
    for _, r in allocation.iterrows():
        alloc_table.add_row(
            str(r["asset"]),
            money(r["market_value"]),
            f"{r['weight_pct']:.1f}%",
        )
    console.print(alloc_table)
    if metrics:
        console.print(f"History metrics ({result['primary_symbol']}): {metrics}")
    console.print(
        f"Projection (year {int(projection.iloc[-1]['year'])}): "
        f"{money(float(projection.iloc[-1]['value']))}"
    )

    if args.export_json:
        payload = {
            "mode": "market-demo",
            "snapshot": snap.model_dump(mode="json"),
            "metrics": metrics,
            "projection": projection.to_dict(orient="records"),
            "provider": result["provider"],
        }
        args.export_json.parent.mkdir(parents=True, exist_ok=True)
        args.export_json.write_text(
            json.dumps(payload, indent=2, default=str), encoding="utf-8"
        )
        console.print(f"[green]Wrote[/green] {args.export_json}")

    console.print("\n[dim]Not financial advice.[/dim]")
    return 0


def main(argv: list[str] | None = None) -> int:
    load_env()
    setup_logging(env_log_level())
    args = build_parser().parse_args(argv)

    use_market = args.market_demo or bool(args.symbols)
    use_worksheet = args.worksheet or args.demo or not use_market

    try:
        if use_market and not (args.worksheet or args.demo):
            return run_market_demo(args)
        if use_market and (args.worksheet or args.demo):
            # both flags: worksheet wins unless only market flags
            return run_worksheet_cli(args)
        if use_worksheet:
            return run_worksheet_cli(args)
        return run_market_demo(args)
    except Exception as exc:
        logger.exception("run failed: %s", exc)
        console.print(f"[red]Error:[/red] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
