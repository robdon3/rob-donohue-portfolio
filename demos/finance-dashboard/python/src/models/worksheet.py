"""Domain models for Financial Worksheet OS (clean-room, multi-view ledger)."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class AccountKind(str, Enum):
    CASH = "cash"
    BROKERAGE = "brokerage"
    RETIREMENT = "retirement"
    HSA = "hsa"
    CRYPTO = "crypto"
    POINTS = "points"
    CREDIT = "credit"
    LOAN = "loan"


class AccountCategory(str, Enum):
    ASSETS = "assets"
    LIABILITIES = "liabilities"
    INVESTMENTS = "investments"


class AssetType(str, Enum):
    CASH = "cash"
    STOCK = "stock"
    RETIREMENT = "retirement"
    HEALTH_SAVINGS = "health_savings"
    CRYPTO = "crypto"
    POINTS = "points"
    CREDIT_DEBT = "credit_debt"
    LOAN_DEBT = "loan_debt"
    OTHER = "other"


class Account(BaseModel):
    id: str
    name: str
    institution: str = "Demo"
    kind: AccountKind
    category: AccountCategory
    credit_limit: Optional[float] = None
    apr_pct: Optional[float] = None


class HoldingLine(BaseModel):
    account_id: str
    asset: str
    ticker: Optional[str] = None
    quantity: float
    price: float
    asset_type: AssetType

    @property
    def value(self) -> float:
        return self.quantity * self.price


class BalanceSnapshot(BaseModel):
    as_of: date
    assets: float
    liabilities: float  # stored negative by convention
    investments: float
    label: Optional[str] = None

    @property
    def net_worth(self) -> float:
        return self.assets + self.liabilities + self.investments


class DebtFacility(BaseModel):
    account_id: str
    name: str
    balance: float  # positive amount owed
    limit: Optional[float] = None
    apr_pct: Optional[float] = None
    utilization_pct: Optional[float] = None
    pct_of_debt: float = 0.0
    payoff_months_est: Optional[float] = None
    payoff_date_est: Optional[date] = None


class WaterfallBucket(BaseModel):
    name: str
    fraction: float = Field(ge=0, le=1)
    amount: float = 0.0


class CashflowPlan(BaseModel):
    net_income_annual: float
    cadence: str = "biweekly"
    paycheck_gross: float
    waterfall: List[WaterfallBucket]
    scenario_name: str = "baseline"


class RunwayStatus(BaseModel):
    monthly_expenses: float
    months_target: float
    target_fund: float
    current_fund: float
    months_covered: float
    deficit: float
    catchup_monthly: float
    catchup_biweekly: float


class CockpitKPIs(BaseModel):
    as_of: date
    assets: float
    liabilities: float
    investments: float
    net_worth: float
    assets_plus_investments: float
    ad_ratio: Optional[float] = None  # assets(+inv) / |liabilities|
    ath_net_worth: Optional[float] = None
    atl_net_worth: Optional[float] = None
    ath_date: Optional[date] = None
    atl_date: Optional[date] = None
    ytd_net_worth_change: Optional[float] = None
    daily_change: Optional[float] = None
    debt_highest: Optional[float] = None
    debt_lowest: Optional[float] = None


class WorksheetBundle(BaseModel):
    """Full multi-view payload for CLI / JSON / browser export."""

    persona_name: str
    disclaimer: str
    generated_at: datetime
    cockpit: CockpitKPIs
    accounts: List[dict]
    holdings: List[dict]
    debt_stack: List[DebtFacility]
    runway: RunwayStatus
    cashflow: CashflowPlan
    scenarios: List[dict]
    ops: dict
    buckets: dict
