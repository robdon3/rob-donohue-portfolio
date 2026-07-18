"""Journal upsert + payments testground (synthetic)."""

from __future__ import annotations

from datetime import date

from src.debt.stack import build_debt_stack
from src.journal.daily import Journal, JournalEntry, upsert_daily_snapshot
from src.ledger.core import load_ledger_from_config
from src.payments.testground import PaymentsTestground, run_payment_scenarios
from src.worksheet.engine import load_synthetic_config, run_worksheet


def test_journal_upsert_overwrite_then_append():
    j = Journal()
    d1 = date(2026, 7, 18)
    assert upsert_daily_snapshot(j, d1, 100, -50, 200) == "append"
    assert len(j.entries) == 1
    assert upsert_daily_snapshot(j, d1, 110, -50, 200, note="rerun") == "overwrite"
    assert len(j.entries) == 1
    assert j.entries[0].assets == 110
    assert j.entries[0].note == "rerun"
    assert upsert_daily_snapshot(j, date(2026, 7, 19), 120, -40, 210) == "append"
    assert len(j.entries) == 2


def test_journal_find_by_date_only():
    j = Journal(
        entries=[
            JournalEntry(date(2026, 1, 1), 1, -1, 1, 1),
            JournalEntry(date(2026, 1, 3), 2, -1, 1, 2),
        ]
    )
    assert j.find_date(date(2026, 1, 2)) is None
    assert j.find_date(date(2026, 1, 3)) == 1


def test_payments_avalanche_prefers_high_apr():
    cfg = load_synthetic_config()
    ledger = load_ledger_from_config(cfg)
    stack = build_debt_stack(ledger, as_of=date(2026, 7, 18))
    tg = PaymentsTestground(stack)
    result = tg.run("t", "avalanche", budget=500)
    assert result.allocations
    # first paid facility should be highest APR among those paid
    paid = [a for a in result.allocations if a["amount"] > 0]
    assert paid
    aprs = {f.account_id: f.apr_pct or 0 for f in stack}
    assert paid[0]["amount"] > 0
    # first in avalanche order should have max APR among facilities with balance
    first_id = paid[0]["account_id"]
    assert aprs[first_id] == max(aprs[f.account_id] for f in stack)


def test_payments_scenarios_from_config():
    cfg = load_synthetic_config()
    ledger = load_ledger_from_config(cfg)
    stack = build_debt_stack(ledger, as_of=date(2026, 7, 18))
    results = run_payment_scenarios(stack, cfg["payments_testground"])
    assert len(results) >= 2
    names = {r["name"] for r in results}
    assert "avalanche_1k" in names


def test_workbook_includes_journal_and_payments():
    bundle = run_worksheet(as_of=date(2026, 7, 18))
    assert bundle.journal_action in ("append", "overwrite")
    assert len(bundle.journal) >= 1
    assert any(r["as_of"] == "2026-07-18" for r in bundle.journal)
    assert len(bundle.payments_testground) >= 1
    assert len(bundle.areas) >= 3
    # same-day overwrite when seed already contains today
    cfg = load_synthetic_config()
    cfg = dict(cfg)
    cfg["journal_seed"] = list(cfg.get("journal_seed") or []) + [
        {
            "as_of": "2026-07-18",
            "assets": 1,
            "liabilities": -1,
            "investments": 1,
            "note": "prior",
        }
    ]
    b2 = run_worksheet(config=cfg, as_of=date(2026, 7, 18))
    assert b2.journal_action == "overwrite"
    today = [r for r in b2.journal if r["as_of"] == "2026-07-18"]
    assert len(today) == 1
    assert today[0]["note"] == "control surface → journal"
