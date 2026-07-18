"""Tests for Financial Worksheet OS (synthetic config, no network)."""

from __future__ import annotations

from datetime import date

from src.cashflow.waterfall import build_cashflow, run_scenarios
from src.debt.stack import build_debt_stack
from src.ledger.core import load_ledger_from_config
from src.runway.fund import compute_runway
from src.snapshots.history import SnapshotStore, cockpit_from_history
from src.worksheet.engine import load_synthetic_config, run_worksheet


def test_load_synthetic_config():
    cfg = load_synthetic_config()
    assert "accounts" in cfg
    assert "holdings" in cfg
    assert "Demo" in cfg["persona"]["name"] or "synthetic" in cfg["persona"]["name"].lower()


def test_ledger_buckets_positive_nw_possible():
    cfg = load_synthetic_config()
    ledger = load_ledger_from_config(cfg)
    buckets = ledger.bucket_totals()
    assert "net_worth" in buckets
    assert buckets["assets_plus_investments"] > 0
    assert buckets["liabilities"] < 0
    hf = ledger.holdings_frame()
    assert len(hf) == len(cfg["holdings"])
    af = ledger.accounts_frame()
    assert len(af) == len(cfg["accounts"])


def test_debt_stack_percentages_sum():
    cfg = load_synthetic_config()
    ledger = load_ledger_from_config(cfg)
    stack = build_debt_stack(ledger, as_of=date(2026, 7, 18))
    assert len(stack) >= 1
    total_pct = sum(d.pct_of_debt for d in stack)
    assert 99.0 <= total_pct <= 101.0


def test_runway_deficit_logic():
    cfg = load_synthetic_config()
    ledger = load_ledger_from_config(cfg)
    rw = compute_runway(ledger, cfg["runway"])
    assert rw.target_fund == rw.monthly_expenses * rw.months_target
    assert rw.months_covered >= 0


def test_cashflow_waterfall_sums_near_paycheck():
    cfg = load_synthetic_config()
    plan = build_cashflow(cfg["cashflow"])
    total = sum(b.amount for b in plan.waterfall)
    assert abs(total - plan.paycheck_gross) < 1.0  # rounding
    scenarios = run_scenarios(cfg["cashflow"])
    assert len(scenarios) >= 2


def test_snapshots_ath_atl():
    cfg = load_synthetic_config()
    store = SnapshotStore.from_config(cfg["snapshots"])
    ath = store.ath()
    atl = store.atl()
    assert ath is not None and atl is not None
    assert ath.net_worth >= atl.net_worth
    ledger = load_ledger_from_config(cfg)
    cockpit = cockpit_from_history(store, ledger.bucket_totals(), as_of=date(2026, 7, 18))
    assert cockpit.net_worth is not None
    assert cockpit.ad_ratio is None or cockpit.ad_ratio > 0


def test_full_worksheet_bundle():
    bundle = run_worksheet(as_of=date(2026, 7, 18))
    assert "Synthetic" in bundle.disclaimer or "synthetic" in bundle.disclaimer.lower()
    assert bundle.cockpit.net_worth != 0
    assert len(bundle.accounts) > 0
    assert len(bundle.holdings) > 0
    assert len(bundle.debt_stack) > 0
    assert bundle.runway.monthly_expenses > 0
    assert bundle.cashflow.paycheck_gross > 0
    assert bundle.ops.get("weekday") is not None
