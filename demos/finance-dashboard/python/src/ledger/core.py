"""
Ledger core — accounts (control plane) + holdings (data plane).

Clean-room: synthetic config only for public demos.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from ..models.worksheet import (
    Account,
    AccountCategory,
    AccountKind,
    AssetType,
    HoldingLine,
)
from ..utils.logging_setup import get_logger

logger = get_logger(__name__)

# Asset types that roll into "investments" bucket (retirement-heavy + marked securities)
INVESTMENT_TYPES = {
    AssetType.RETIREMENT,
    AssetType.STOCK,
}
LIABILITY_TYPES = {AssetType.CREDIT_DEBT, AssetType.LOAN_DEBT}


class Ledger:
    """In-memory multi-account ledger with rollups."""

    def __init__(
        self,
        accounts: List[Account],
        holdings: List[HoldingLine],
        persona_name: str = "Demo Household",
        disclaimer: str = "Synthetic data.",
    ) -> None:
        self.accounts = {a.id: a for a in accounts}
        self.holdings = holdings
        self.persona_name = persona_name
        self.disclaimer = disclaimer

    def account(self, account_id: str) -> Optional[Account]:
        return self.accounts.get(account_id)

    def holdings_frame(self) -> pd.DataFrame:
        rows = []
        for h in self.holdings:
            acct = self.accounts.get(h.account_id)
            rows.append(
                {
                    "account_id": h.account_id,
                    "account_name": acct.name if acct else h.account_id,
                    "institution": acct.institution if acct else "",
                    "account_kind": acct.kind.value if acct else "",
                    "asset": h.asset,
                    "ticker": h.ticker or "",
                    "quantity": h.quantity,
                    "price": h.price,
                    "value": h.value,
                    "asset_type": h.asset_type.value,
                    "is_liability": h.asset_type in LIABILITY_TYPES,
                }
            )
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        total_pos = df.loc[~df["is_liability"], "value"].sum()
        df["pct_of_assets"] = df.apply(
            lambda r: (r["value"] / total_pos * 100)
            if not r["is_liability"] and total_pos
            else None,
            axis=1,
        )
        return df

    def accounts_frame(self) -> pd.DataFrame:
        """One row per account with rolled balance."""
        hf = self.holdings_frame()
        rows = []
        for aid, acct in self.accounts.items():
            subset = hf[hf["account_id"] == aid] if not hf.empty else pd.DataFrame()
            if subset.empty:
                bal = 0.0
            elif acct.category == AccountCategory.LIABILITIES:
                bal = float(subset["value"].sum())  # amount owed (positive)
            else:
                bal = float(subset["value"].sum())
            rows.append(
                {
                    "account_id": aid,
                    "name": acct.name,
                    "institution": acct.institution,
                    "kind": acct.kind.value,
                    "category": acct.category.value,
                    "balance": bal,
                    "credit_limit": acct.credit_limit,
                    "apr_pct": acct.apr_pct,
                    "utilization_pct": (
                        (bal / acct.credit_limit * 100)
                        if acct.credit_limit and acct.kind == AccountKind.CREDIT
                        else None
                    ),
                }
            )
        return pd.DataFrame(rows)

    def bucket_totals(self) -> Dict[str, float]:
        """
        Worksheet-style buckets:
          assets     = cash, hsa, points, crypto, brokerage cash/stock (non-retirement)
          investments = retirement + optional stock classification
          liabilities = credit + loan (negative)
        """
        assets = 0.0
        investments = 0.0
        liabilities = 0.0

        for h in self.holdings:
            v = h.value
            if h.asset_type in LIABILITY_TYPES:
                liabilities -= abs(v)
            elif h.asset_type == AssetType.RETIREMENT:
                investments += v
            elif h.asset_type == AssetType.STOCK:
                # Count equities under assets+investments split used by cockpit
                investments += v
            else:
                assets += v

        return {
            "assets": round(assets, 2),
            "investments": round(investments, 2),
            "liabilities": round(liabilities, 2),
            "net_worth": round(assets + investments + liabilities, 2),
            "assets_plus_investments": round(assets + investments, 2),
        }

    def home_buckets(self) -> Dict[str, float]:
        """Phone/Home-style high-level sleeves."""
        out = {
            "cash": 0.0,
            "stocks": 0.0,
            "retirement": 0.0,
            "crypto": 0.0,
            "points": 0.0,
            "health_savings": 0.0,
            "credit_debt": 0.0,
            "loan_debt": 0.0,
        }
        for h in self.holdings:
            key = h.asset_type.value
            if key in out:
                if h.asset_type in LIABILITY_TYPES:
                    out[key] += abs(h.value)
                else:
                    out[key] += h.value
        return {k: round(v, 2) for k, v in out.items()}

    def cash_in_accounts(self, account_ids: List[str]) -> float:
        total = 0.0
        for h in self.holdings:
            if h.account_id in account_ids and h.asset_type not in LIABILITY_TYPES:
                total += h.value
        return total


def load_ledger_from_config(cfg: Dict[str, Any]) -> Ledger:
    persona = cfg.get("persona", {})
    accounts = [
        Account(
            id=a["id"],
            name=a["name"],
            institution=a.get("institution", "Demo"),
            kind=AccountKind(a["kind"]),
            category=AccountCategory(a["category"]),
            credit_limit=a.get("credit_limit"),
            apr_pct=a.get("apr_pct"),
        )
        for a in cfg.get("accounts", [])
    ]
    holdings = [
        HoldingLine(
            account_id=h["account_id"],
            asset=h["asset"],
            ticker=h.get("ticker"),
            quantity=float(h["quantity"]),
            price=float(h["price"]),
            asset_type=AssetType(h["asset_type"]),
        )
        for h in cfg.get("holdings", [])
    ]
    logger.info(
        "ledger loaded accounts=%s holdings=%s persona=%s",
        len(accounts),
        len(holdings),
        persona.get("name"),
    )
    return Ledger(
        accounts=accounts,
        holdings=holdings,
        persona_name=persona.get("name", "Demo Household"),
        disclaimer=persona.get(
            "disclaimer", "Synthetic data for portfolio evaluation."
        ),
    )
