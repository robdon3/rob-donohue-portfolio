"""Expense runway / 6-month fund catch-up math."""

from __future__ import annotations

from typing import Any, Dict, List

from ..ledger.core import Ledger
from ..models.worksheet import RunwayStatus
from ..utils.logging_setup import get_logger

logger = get_logger(__name__)


def compute_runway(ledger: Ledger, runway_cfg: Dict[str, Any]) -> RunwayStatus:
    monthly = float(runway_cfg.get("monthly_expenses", 0))
    months_target = float(runway_cfg.get("months_target", 6))
    target = monthly * months_target
    fund_ids: List[str] = list(runway_cfg.get("fund_account_ids") or [])
    current = ledger.cash_in_accounts(fund_ids) if fund_ids else 0.0
    months_covered = (current / monthly) if monthly else 0.0
    deficit = max(target - current, 0.0)
    catchup_m = deficit  # one-shot "months to fill" at full deficit / 1 month framing
    # Catch-up as monthly payment to fill deficit over remaining implicit horizon:
    # demo: fill deficit over next 12 months if behind
    catchup_monthly = deficit / 12.0 if deficit else 0.0
    catchup_biweekly = catchup_monthly / 2.0

    status = RunwayStatus(
        monthly_expenses=round(monthly, 2),
        months_target=months_target,
        target_fund=round(target, 2),
        current_fund=round(current, 2),
        months_covered=round(months_covered, 2),
        deficit=round(deficit, 2),
        catchup_monthly=round(catchup_monthly, 2),
        catchup_biweekly=round(catchup_biweekly, 2),
    )
    logger.info(
        "runway fund=%.2f target=%.2f months_covered=%.2f",
        status.current_fund,
        status.target_fund,
        status.months_covered,
    )
    return status
