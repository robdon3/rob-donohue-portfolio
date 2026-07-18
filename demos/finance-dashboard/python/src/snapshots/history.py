"""
Append-style balance snapshot history → ATH / ATL / YTD / daily Δ.

Design: snapshots are first-class time series, not overwritten cells.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from ..models.worksheet import BalanceSnapshot, CockpitKPIs
from ..utils.logging_setup import get_logger

logger = get_logger(__name__)


class SnapshotStore:
    def __init__(self, snapshots: List[BalanceSnapshot]) -> None:
        self._snaps = sorted(snapshots, key=lambda s: s.as_of)

    @classmethod
    def from_config(cls, rows: List[Dict[str, Any]]) -> "SnapshotStore":
        snaps = [
            BalanceSnapshot(
                as_of=date.fromisoformat(str(r["as_of"])[:10]),
                assets=float(r["assets"]),
                liabilities=float(r["liabilities"]),
                investments=float(r["investments"]),
                label=r.get("label"),
            )
            for r in rows
        ]
        return cls(snaps)

    def all(self) -> List[BalanceSnapshot]:
        return list(self._snaps)

    def append_live(self, live: BalanceSnapshot) -> None:
        """Attach today's computed ledger totals as latest snapshot."""
        # Replace same-day if present
        self._snaps = [s for s in self._snaps if s.as_of != live.as_of]
        self._snaps.append(live)
        self._snaps.sort(key=lambda s: s.as_of)

    def ath(self) -> Optional[BalanceSnapshot]:
        if not self._snaps:
            return None
        return max(self._snaps, key=lambda s: s.net_worth)

    def atl(self) -> Optional[BalanceSnapshot]:
        if not self._snaps:
            return None
        return min(self._snaps, key=lambda s: s.net_worth)

    def debt_extremes(self) -> Tuple[Optional[float], Optional[float]]:
        """Liabilities are negative; highest debt = most negative; lowest = closest to zero."""
        if not self._snaps:
            return None, None
        debts = [s.liabilities for s in self._snaps]
        return min(debts), max(debts)  # min = most debt, max = least debt (less negative)

    def year_start(self, year: int) -> Optional[BalanceSnapshot]:
        candidates = [s for s in self._snaps if s.as_of.year < year]
        if not candidates:
            # first snap in year
            year_snaps = [s for s in self._snaps if s.as_of.year == year]
            return year_snaps[0] if year_snaps else None
        return max(candidates, key=lambda s: s.as_of)

    def latest(self) -> Optional[BalanceSnapshot]:
        return self._snaps[-1] if self._snaps else None

    def previous(self) -> Optional[BalanceSnapshot]:
        return self._snaps[-2] if len(self._snaps) >= 2 else None


def cockpit_from_history(
    store: SnapshotStore,
    live_buckets: Dict[str, float],
    as_of: Optional[date] = None,
) -> CockpitKPIs:
    as_of = as_of or date.today()
    live = BalanceSnapshot(
        as_of=as_of,
        assets=float(live_buckets["assets"]),
        liabilities=float(live_buckets["liabilities"]),
        investments=float(live_buckets["investments"]),
        label="live",
    )
    store.append_live(live)

    ath = store.ath()
    atl = store.atl()
    debt_hi, debt_lo = store.debt_extremes()
    ys = store.year_start(as_of.year)
    prev = store.previous()

    assets = live.assets
    liab = live.liabilities
    inv = live.investments
    nw = live.net_worth
    a_plus_i = assets + inv
    ad = (a_plus_i / abs(liab)) if liab else None

    ytd = (nw - ys.net_worth) if ys else None
    daily = (nw - prev.net_worth) if prev else None

    kpis = CockpitKPIs(
        as_of=as_of,
        assets=round(assets, 2),
        liabilities=round(liab, 2),
        investments=round(inv, 2),
        net_worth=round(nw, 2),
        assets_plus_investments=round(a_plus_i, 2),
        ad_ratio=round(ad, 2) if ad is not None else None,
        ath_net_worth=round(ath.net_worth, 2) if ath else None,
        atl_net_worth=round(atl.net_worth, 2) if atl else None,
        ath_date=ath.as_of if ath else None,
        atl_date=atl.as_of if atl else None,
        ytd_net_worth_change=round(ytd, 2) if ytd is not None else None,
        daily_change=round(daily, 2) if daily is not None else None,
        debt_highest=round(debt_hi, 2) if debt_hi is not None else None,
        debt_lowest=round(debt_lo, 2) if debt_lo is not None else None,
    )
    logger.info(
        "cockpit NW=%.2f ATH=%.2f ATL=%.2f A/D=%s",
        kpis.net_worth,
        kpis.ath_net_worth or 0,
        kpis.atl_net_worth or 0,
        kpis.ad_ratio,
    )
    return kpis
