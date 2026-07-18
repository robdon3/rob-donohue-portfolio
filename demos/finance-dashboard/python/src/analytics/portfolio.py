"""
Portfolio analytics — pure functions over DataFrames.

Keeps calculations out of adapters so models/assumptions are reviewable.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from ..models.domain import PortfolioSnapshot
from ..utils.logging_setup import get_logger

logger = get_logger(__name__)


class PortfolioAnalytics:
    """Valuation, allocation, simple projections, risk-ish metrics."""

    def __init__(
        self,
        expected_annual_return: float = 0.07,
        projection_years: int = 10,
        risk_free_rate: float = 0.04,
    ) -> None:
        self.expected_annual_return = expected_annual_return
        self.projection_years = projection_years
        self.risk_free_rate = risk_free_rate

    def snapshot(
        self,
        name: str,
        positions: pd.DataFrame,
        cash: float,
    ) -> PortfolioSnapshot:
        if positions.empty:
            return PortfolioSnapshot(
                name=name,
                as_of=datetime.now(timezone.utc),
                cash=cash,
                total_market_value=cash,
                total_cost=0.0,
                unrealized_pnl=0.0,
                unrealized_pnl_pct=0.0,
                positions=[],
            )

        equity_mv = float(positions["market_value"].fillna(0).sum())
        total_cost = float(positions["cost_total"].fillna(0).sum())
        total_mv = equity_mv + cash
        pnl = equity_mv - total_cost
        pnl_pct = (pnl / total_cost * 100) if total_cost else 0.0

        # Recompute weights including cash
        pos_records = positions.copy()
        pos_records["weight_pct"] = (
            pos_records["market_value"].fillna(0) / total_mv * 100 if total_mv else 0
        )

        snap = PortfolioSnapshot(
            name=name,
            as_of=datetime.now(timezone.utc),
            cash=cash,
            total_market_value=round(total_mv, 2),
            total_cost=round(total_cost, 2),
            unrealized_pnl=round(pnl, 2),
            unrealized_pnl_pct=round(pnl_pct, 3),
            positions=pos_records.replace({np.nan: None}).to_dict(orient="records"),
        )
        logger.info(
            "snapshot %s total=%.2f pnl=%.2f (%.2f%%)",
            name,
            snap.total_market_value,
            snap.unrealized_pnl,
            snap.unrealized_pnl_pct,
        )
        return snap

    def allocation_table(self, positions: pd.DataFrame, cash: float) -> pd.DataFrame:
        """Allocation including cash sleeve."""
        rows: List[Dict[str, Any]] = []
        equity_mv = float(positions["market_value"].fillna(0).sum()) if not positions.empty else 0.0
        total = equity_mv + cash
        if not positions.empty:
            for _, r in positions.iterrows():
                mv = float(r["market_value"] or 0)
                rows.append(
                    {
                        "asset": r["symbol"],
                        "market_value": mv,
                        "weight_pct": (mv / total * 100) if total else 0,
                        "kind": "equity_or_crypto",
                    }
                )
        rows.append(
            {
                "asset": "CASH",
                "market_value": cash,
                "weight_pct": (cash / total * 100) if total else 0,
                "kind": "cash",
            }
        )
        return pd.DataFrame(rows)

    def project_growth(
        self,
        present_value: float,
        years: int | None = None,
        annual_return: float | None = None,
        annual_contribution: float = 0.0,
    ) -> pd.DataFrame:
        """
        Simple year-end projection (educational — not financial advice).

        Uses compound growth + optional annual contribution at year end.
        Extension: Monte Carlo, glide paths, fee drag, tax.
        """
        years = years if years is not None else self.projection_years
        r = annual_return if annual_return is not None else self.expected_annual_return
        value = present_value
        rows = [{"year": 0, "value": round(value, 2), "assumed_return": r}]
        for y in range(1, years + 1):
            value = value * (1 + r) + annual_contribution
            rows.append({"year": y, "value": round(value, 2), "assumed_return": r})
        return pd.DataFrame(rows)

    def history_returns(self, history: pd.DataFrame) -> pd.DataFrame:
        """Daily returns + cumulative from close prices."""
        if history.empty or "close" not in history.columns:
            return pd.DataFrame()
        df = history[["bar_date", "close"]].copy()
        df["daily_return"] = df["close"].pct_change()
        df["cumulative"] = (1 + df["daily_return"].fillna(0)).cumprod() - 1
        return df

    def summary_metrics(self, history: pd.DataFrame) -> Dict[str, float]:
        """Rough demo metrics from a single-asset history series."""
        rets = self.history_returns(history)
        if rets.empty or rets["daily_return"].dropna().empty:
            return {}
        daily = rets["daily_return"].dropna()
        # annualize with ~252 trading days
        vol = float(daily.std() * np.sqrt(252))
        mean = float(daily.mean() * 252)
        sharpe = (
            (mean - self.risk_free_rate) / vol if vol > 1e-9 else 0.0
        )
        return {
            "ann_return_est": round(mean, 4),
            "ann_vol_est": round(vol, 4),
            "sharpe_approx": round(sharpe, 3),
            "max_drawdown": round(self._max_drawdown(rets["close"]), 4),
        }

    @staticmethod
    def _max_drawdown(prices: pd.Series) -> float:
        if prices.empty:
            return 0.0
        peak = prices.cummax()
        dd = (prices - peak) / peak
        return float(dd.min())
