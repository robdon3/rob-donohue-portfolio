"""
ETL spine: Extract (client) → Transform (normalize) → Load (DataFrames / optional files).

Design trade-off:
  Keep transforms pure (no I/O) where possible so unit tests stay fast.
  I/O lives at the edges (client + optional cache/export).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import pandas as pd

from ..clients.base import MarketDataClient
from ..models.domain import Holding, MarketQuote, PriceBar
from ..utils.logging_setup import get_logger

logger = get_logger(__name__)


class FinanceETLPipeline:
    """Orchestrates market data pull and normalization for analytics."""

    def __init__(
        self,
        client: MarketDataClient,
        cache_dir: Optional[Path] = None,
    ) -> None:
        self.client = client
        self.cache_dir = cache_dir
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    # ---- Extract ----------------------------------------------------------

    def extract_quotes(self, symbols: Sequence[str]) -> List[MarketQuote]:
        logger.info(
            "extract quotes provider=%s symbols=%s",
            self.client.name,
            list(symbols),
        )
        return self.client.get_quotes(symbols)

    def extract_history(self, symbol: str, days: int = 90) -> List[PriceBar]:
        logger.info("extract history %s days=%s", symbol, days)
        return self.client.get_history(symbol, days=days)

    # ---- Transform --------------------------------------------------------

    @staticmethod
    def quotes_to_frame(quotes: List[MarketQuote]) -> pd.DataFrame:
        """Normalize quotes → tabular form (one row per symbol)."""
        rows = [q.model_dump() for q in quotes]
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        df["symbol"] = df["symbol"].str.upper()
        df["as_of"] = pd.to_datetime(df["as_of"], utc=True)
        return df.sort_values("symbol").reset_index(drop=True)

    @staticmethod
    def history_to_frame(bars: List[PriceBar]) -> pd.DataFrame:
        rows = [b.model_dump() for b in bars]
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        df["bar_date"] = pd.to_datetime(df["bar_date"])
        return df.sort_values("bar_date").reset_index(drop=True)

    @staticmethod
    def enrich_positions(
        holdings: List[Holding],
        quotes: List[MarketQuote],
    ) -> pd.DataFrame:
        """
        Join holdings with live quotes → position-level P&amp;L.

        Extension point: add FX conversion, lots, fees, tax lots.
        """
        quote_map: Dict[str, MarketQuote] = {q.symbol.upper(): q for q in quotes}
        rows = []
        for h in holdings:
            q = quote_map.get(h.symbol.upper())
            price = q.price if q else None
            market_value = (price * h.shares) if price is not None else None
            cost = h.cost_basis * h.shares
            pnl = (market_value - cost) if market_value is not None else None
            pnl_pct = (pnl / cost * 100) if pnl is not None and cost else None
            weight_placeholder = market_value  # filled after total known
            rows.append(
                {
                    "symbol": h.symbol.upper(),
                    "shares": h.shares,
                    "cost_basis": h.cost_basis,
                    "cost_total": cost,
                    "price": price,
                    "market_value": market_value,
                    "unrealized_pnl": pnl,
                    "unrealized_pnl_pct": pnl_pct,
                    "day_change_pct": q.change_pct if q else None,
                    "quote_source": q.source if q else None,
                    "weight_placeholder": weight_placeholder,
                }
            )
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        total_mv = df["market_value"].fillna(0).sum()
        df["weight_pct"] = (
            df["market_value"].fillna(0) / total_mv * 100 if total_mv else 0
        )
        df = df.drop(columns=["weight_placeholder"])
        return df

    # ---- Load -------------------------------------------------------------

    def load_csv(self, df: pd.DataFrame, name: str) -> Optional[Path]:
        """Optional artifact write for audit / Streamlit later."""
        if self.cache_dir is None or df.empty:
            return None
        path = self.cache_dir / f"{name}.csv"
        df.to_csv(path, index=False)
        logger.info("wrote artifact %s rows=%s", path, len(df))
        return path

    # ---- Full run ---------------------------------------------------------

    def run_portfolio_etl(
        self,
        holdings: List[Holding],
        history_days: int = 90,
        primary_symbol: Optional[str] = None,
    ) -> dict:
        """
        End-to-end extract/transform for a portfolio.

        Returns dict of DataFrames + metadata for analytics/CLI.
        """
        symbols = [h.symbol for h in holdings]
        quotes = self.extract_quotes(symbols)
        quotes_df = self.quotes_to_frame(quotes)
        positions_df = self.enrich_positions(holdings, quotes)

        primary = primary_symbol or (symbols[0] if symbols else "AAPL")
        history = self.extract_history(primary, days=history_days)
        history_df = self.history_to_frame(history)

        self.load_csv(quotes_df, "quotes")
        self.load_csv(positions_df, "positions")
        self.load_csv(history_df, f"history_{primary}")

        return {
            "as_of": datetime.now(timezone.utc),
            "provider": self.client.name,
            "quotes": quotes_df,
            "positions": positions_df,
            "history": history_df,
            "primary_symbol": primary,
        }
