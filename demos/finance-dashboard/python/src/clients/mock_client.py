"""Deterministic mock market data — always works offline (CI / demos / interviews)."""

from __future__ import annotations

import hashlib
import math
from datetime import date, datetime, timedelta, timezone
from typing import List, Sequence

from ..models.domain import MarketQuote, PriceBar
from ..utils.logging_setup import get_logger
from .base import MarketDataClient

logger = get_logger(__name__)

# Seed prices for common demo symbols (extend as needed)
_SEED_PRICES = {
    "AAPL": 190.0,
    "MSFT": 420.0,
    "GOOGL": 175.0,
    "AMZN": 185.0,
    "BTC-USD": 65000.0,
    "ETH-USD": 3400.0,
    "VTI": 260.0,
    "VOO": 480.0,
    "SPY": 520.0,
}


class MockMarketClient(MarketDataClient):
    """Synthetic but realistic-looking series for architecture demos."""

    name = "mock"

    def get_quotes(self, symbols: Sequence[str]) -> List[MarketQuote]:
        now = datetime.now(timezone.utc)
        quotes: List[MarketQuote] = []
        for sym in symbols:
            price = self._price_for(sym, now.date())
            prev = self._price_for(sym, now.date() - timedelta(days=1))
            change = ((price - prev) / prev) * 100 if prev else 0.0
            quotes.append(
                MarketQuote(
                    symbol=sym.upper(),
                    price=round(price, 4),
                    as_of=now,
                    change_pct=round(change, 3),
                    volume=1_000_000 + self._hash_int(sym) % 500_000,
                    source=self.name,
                )
            )
        logger.info("mock quotes generated for %s symbols", len(quotes))
        return quotes

    def get_history(self, symbol: str, days: int = 90) -> List[PriceBar]:
        symbol = symbol.upper()
        end = date.today()
        bars: List[PriceBar] = []
        for i in range(days, 0, -1):
            d = end - timedelta(days=i)
            # skip synthetic weekends for equity-like feel
            if d.weekday() >= 5 and not symbol.endswith("-USD"):
                continue
            close = self._price_for(symbol, d)
            open_p = close * (1 - 0.003 * math.sin(i))
            high = max(open_p, close) * 1.005
            low = min(open_p, close) * 0.995
            bars.append(
                PriceBar(
                    symbol=symbol,
                    bar_date=d,
                    open=round(open_p, 4),
                    high=round(high, 4),
                    low=round(low, 4),
                    close=round(close, 4),
                    volume=float(800_000 + self._hash_int(f"{symbol}{d}") % 400_000),
                )
            )
        logger.debug("mock history %s bars=%s", symbol, len(bars))
        return bars

    def _price_for(self, symbol: str, on: date) -> float:
        base = _SEED_PRICES.get(symbol.upper(), 100.0 + (self._hash_int(symbol) % 50))
        # smooth drift + mild oscillation (deterministic)
        day_index = on.toordinal()
        drift = 1 + 0.0002 * ((day_index % 365) - 180)
        wave = 1 + 0.02 * math.sin(day_index / 12.0 + self._hash_int(symbol) % 7)
        noise = 1 + 0.005 * math.sin(day_index * 0.7 + self._hash_int(symbol))
        return base * drift * wave * noise

    @staticmethod
    def _hash_int(value: str) -> int:
        return int(hashlib.md5(value.encode()).hexdigest()[:8], 16)
