"""Domain models — stable contracts across adapters and analytics."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Holding(BaseModel):
    """A single position in the portfolio."""

    symbol: str
    shares: float = Field(gt=0)
    cost_basis: float = Field(ge=0, description="Average cost per share")


class MarketQuote(BaseModel):
    """Latest quote normalized across providers."""

    symbol: str
    price: float
    currency: str = "USD"
    as_of: datetime
    change_pct: Optional[float] = None
    volume: Optional[float] = None
    source: str = "unknown"


class PriceBar(BaseModel):
    """OHLCV bar for time-series analytics."""

    symbol: str
    bar_date: date
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class PortfolioSnapshot(BaseModel):
    """Point-in-time valuation of holdings + cash."""

    name: str
    as_of: datetime
    cash: float
    total_market_value: float
    total_cost: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    positions: List[dict]
