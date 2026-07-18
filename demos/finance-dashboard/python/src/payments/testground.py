"""
Payments testground — purpose-built sandbox for payment strategy.

Not a banking product. A place to try allocation rules, card routing,
and "what if I throw X at this facility" without touching the live ledger.

In the real workbook this is a dedicated area; here it's a module with
clear inputs/outputs so the strategy stays inspectable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..models.worksheet import DebtFacility
from ..utils.logging_setup import get_logger

logger = get_logger(__name__)


@dataclass
class PaymentScenarioResult:
    name: str
    description: str
    total_payment: float
    allocations: List[dict]  # facility, amount, remaining, rule
    projected_total_debt: float


class PaymentsTestground:
    """
    Apply a payment budget across the debt stack under named strategies.

    Strategies (demo):
      - avalanche: highest APR first
      - snowball: smallest balance first
      - weighted: proportional to balance
      - directed: fixed map of account_id → amount (config)
    """

    def __init__(self, facilities: List[DebtFacility]) -> None:
        self.facilities = list(facilities)

    def run(
        self,
        name: str,
        strategy: str,
        budget: float,
        directed: Optional[Dict[str, float]] = None,
        description: str = "",
    ) -> PaymentScenarioResult:
        strategy = strategy.lower().strip()
        remaining_budget = float(budget)
        # working copy of balances
        bals = {f.account_id: f.balance for f in self.facilities}
        meta = {f.account_id: f for f in self.facilities}
        order = list(self.facilities)

        if strategy == "avalanche":
            order = sorted(order, key=lambda f: (f.apr_pct or 0), reverse=True)
        elif strategy == "snowball":
            order = sorted(order, key=lambda f: f.balance)
        elif strategy == "weighted":
            order = list(self.facilities)
        elif strategy == "directed":
            order = list(self.facilities)
        else:
            raise ValueError(f"Unknown payment strategy: {strategy}")

        allocations: List[dict] = []

        if strategy == "directed":
            directed = directed or {}
            for acct_id, amt in directed.items():
                if acct_id not in bals:
                    continue
                pay = min(float(amt), bals[acct_id], remaining_budget)
                bals[acct_id] -= pay
                remaining_budget -= pay
                allocations.append(
                    {
                        "account_id": acct_id,
                        "name": meta[acct_id].name,
                        "amount": round(pay, 2),
                        "remaining": round(bals[acct_id], 2),
                        "rule": "directed",
                    }
                )
        elif strategy == "weighted":
            total = sum(bals.values()) or 1.0
            for f in order:
                share = bals[f.account_id] / total
                pay = min(budget * share, bals[f.account_id])
                bals[f.account_id] -= pay
                allocations.append(
                    {
                        "account_id": f.account_id,
                        "name": f.name,
                        "amount": round(pay, 2),
                        "remaining": round(bals[f.account_id], 2),
                        "rule": "weighted",
                    }
                )
        else:
            # avalanche / snowball: waterfill in order
            for f in order:
                if remaining_budget <= 0:
                    break
                pay = min(remaining_budget, bals[f.account_id])
                bals[f.account_id] -= pay
                remaining_budget -= pay
                allocations.append(
                    {
                        "account_id": f.account_id,
                        "name": f.name,
                        "amount": round(pay, 2),
                        "remaining": round(bals[f.account_id], 2),
                        "rule": strategy,
                    }
                )

        projected = round(sum(bals.values()), 2)
        used = round(budget - remaining_budget if strategy != "weighted" else sum(a["amount"] for a in allocations), 2)
        logger.info(
            "payments testground strategy=%s budget=%.2f used=%.2f projected_debt=%.2f",
            strategy,
            budget,
            used,
            projected,
        )
        return PaymentScenarioResult(
            name=name,
            description=description or strategy,
            total_payment=used if strategy != "weighted" else round(sum(a["amount"] for a in allocations), 2),
            allocations=allocations,
            projected_total_debt=projected,
        )


def run_payment_scenarios(
    facilities: List[DebtFacility],
    scenarios: List[Dict[str, Any]],
) -> List[dict]:
    tg = PaymentsTestground(facilities)
    out = []
    for sc in scenarios:
        result = tg.run(
            name=sc.get("name", "scenario"),
            strategy=sc.get("strategy", "avalanche"),
            budget=float(sc.get("budget", 0)),
            directed=sc.get("directed"),
            description=sc.get("description", ""),
        )
        out.append(
            {
                "name": result.name,
                "description": result.description,
                "total_payment": result.total_payment,
                "projected_total_debt": result.projected_total_debt,
                "allocations": result.allocations,
            }
        )
    return out
