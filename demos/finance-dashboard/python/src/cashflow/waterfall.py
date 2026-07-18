"""Paycheck waterfall + scenario multipliers (educational)."""

from __future__ import annotations

from typing import Any, Dict, List

from ..models.worksheet import CashflowPlan, WaterfallBucket
from ..utils.logging_setup import get_logger

logger = get_logger(__name__)

PAYCHECKS_PER_YEAR = {
    "weekly": 52,
    "biweekly": 26,
    "semimonthly": 24,
    "monthly": 12,
}


def build_cashflow(
    cashflow_cfg: Dict[str, Any],
    scenario_name: str = "baseline",
    income_multiplier: float = 1.0,
    debt_extra: float = 0.0,
) -> CashflowPlan:
    annual = float(cashflow_cfg.get("net_income_annual", 0)) * income_multiplier
    cadence = str(cashflow_cfg.get("cadence", "biweekly")).lower()
    n = PAYCHECKS_PER_YEAR.get(cadence, 26)
    paycheck = annual / n

    buckets: List[WaterfallBucket] = []
    for b in cashflow_cfg.get("waterfall", []):
        frac = float(b["fraction"])
        buckets.append(
            WaterfallBucket(
                name=b["name"],
                fraction=frac,
                amount=round(paycheck * frac, 2),
            )
        )

    # Optional extra to debt payment bucket
    if debt_extra:
        for bucket in buckets:
            if "debt" in bucket.name.lower():
                bucket.amount = round(bucket.amount + debt_extra, 2)
                break
        else:
            buckets.append(
                WaterfallBucket(
                    name="Extra debt payment",
                    fraction=0.0,
                    amount=round(debt_extra, 2),
                )
            )

    plan = CashflowPlan(
        net_income_annual=round(annual, 2),
        cadence=cadence,
        paycheck_gross=round(paycheck, 2),
        waterfall=buckets,
        scenario_name=scenario_name,
    )
    logger.info(
        "cashflow scenario=%s paycheck=%.2f buckets=%s",
        scenario_name,
        plan.paycheck_gross,
        len(buckets),
    )
    return plan


def run_scenarios(cashflow_cfg: Dict[str, Any]) -> List[dict]:
    scenarios = cashflow_cfg.get("scenarios") or [
        {"name": "baseline", "income_multiplier": 1.0, "debt_extra": 0.0}
    ]
    out = []
    for sc in scenarios:
        plan = build_cashflow(
            cashflow_cfg,
            scenario_name=sc.get("name", "scenario"),
            income_multiplier=float(sc.get("income_multiplier", 1.0)),
            debt_extra=float(sc.get("debt_extra", 0.0)),
        )
        out.append(
            {
                "name": plan.scenario_name,
                "paycheck": plan.paycheck_gross,
                "annual": plan.net_income_annual,
                "waterfall": [b.model_dump() for b in plan.waterfall],
            }
        )
    return out
