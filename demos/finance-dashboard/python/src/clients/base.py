"""Market data client protocol — implement this to add a new provider."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Sequence

from ..models.domain import MarketQuote, PriceBar


class MarketDataClient(ABC):
    """
    Adapter interface for market data.

    Design note:
      All providers return the same domain models so ETL/analytics
      never branch on vendor-specific payloads.
    """

    name: str = "base"

    @abstractmethod
    def get_quotes(self, symbols: Sequence[str]) -> List[MarketQuote]:
        """Fetch latest quotes for symbols."""

    @abstractmethod
    def get_history(self, symbol: str, days: int = 90) -> List[PriceBar]:
        """Fetch daily history for a single symbol."""
