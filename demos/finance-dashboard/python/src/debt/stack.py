"""Debt stack analytics — utilization, % of debt, simple payoff clocks."""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional

from ..ledger.core import Ledger
from ..models.worksheet import AccountKind, AssetType, DebtFacility
from ..utils.logging_setup import get_logger

logger = get_logger(__name__)


def _payoff_months(
    balance: float,
    apr_pct: Optional[float],
    monthly_payment: Optional[float] = None,
) -> Optional[float]:
    """
    Rough payoff months: if payment omitted, assume 2% of balance or $50 min.
    Educational demo math — not a lending product.
    """
    if balance <= 0:
        return 0.0
    r = (apr_pct or 0.0) / 100.0 / 12.0
    pay = monthly_payment
    if pay is None:
        pay = max(balance * 0.02, 50.0)
    if pay <= 0:
        return None
    if r <= 0:
        return balance / pay
    # n = log(pay / (pay - r*B)) / log(1+r)
    if pay <= r * balance:
        return None  # never pays off at this payment
    import math

    n = math.log(pay / (pay - r * balance)) / math.log(1 + r)
    return round(n, 2)


def build_debt_stack(
    ledger: Ledger,
    as_of: Optional[date] = None,
) -> List[DebtFacility]:
    as_of = as_of or date.today()
    facilities: List[DebtFacility] = []
    total_debt = 0.0

    for h in ledger.holdings:
        if h.asset_type not in (AssetType.CREDIT_DEBT, AssetType.LOAN_DEBT):
            continue
        acct = ledger.account(h.account_id)
        bal = abs(h.value)
        total_debt += bal
        limit = acct.credit_limit if acct else None
        apr = acct.apr_pct if acct else None
        util = (bal / limit * 100) if limit else None
        months = _payoff_months(bal, apr)
        payoff_date = (
            as_of + timedelta(days=int(months * 30.44)) if months is not None else None
        )
        facilities.append(
            DebtFacility(
                account_id=h.account_id,
                name=acct.name if acct else h.account_id,
                balance=round(bal, 2),
                limit=limit,
                apr_pct=apr,
                utilization_pct=round(util, 2) if util is not None else None,
                pct_of_debt=0.0,
                payoff_months_est=months,
                payoff_date_est=payoff_date,
            )
        )

    if total_debt > 0:
        for f in facilities:
            f.pct_of_debt = round(f.balance / total_debt * 100, 2)

    facilities.sort(key=lambda x: x.balance, reverse=True)
    logger.info("debt stack facilities=%s total=%.2f", len(facilities), total_debt)
    return facilities
