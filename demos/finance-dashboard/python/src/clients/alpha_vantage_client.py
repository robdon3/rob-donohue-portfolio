"""Alpha Vantage adapter — requires ALPHA_VANTAGE_API_KEY (free tier available)."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import List, Sequence

import httpx

from ..models.domain import MarketQuote, PriceBar
from ..utils.logging_setup import get_logger
from ..utils.retry import retry_with_backoff
from .base import MarketDataClient

logger = get_logger(__name__)

BASE_URL = "https://www.alphavantage.co/query"


class AlphaVantageClient(MarketDataClient):
    """
    REST client for Alpha Vantage GLOBAL_QUOTE + TIME_SERIES_DAILY.

    Free tier rate limits are strict — cache aggressively in ETL for demos.
    Extension: add premium endpoints without changing analytics consumers.
    """

    name = "alpha_vantage"

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 15.0,
    ) -> None:
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "ALPHA_VANTAGE_API_KEY is required for alpha_vantage provider. "
                "Set env or use FINANCE_PROVIDER=mock"
            )
        self.timeout = timeout

    def get_quotes(self, symbols: Sequence[str]) -> List[MarketQuote]:
        quotes: List[MarketQuote] = []
        for sym in symbols:
            try:
                quotes.append(self._global_quote(sym))
            except Exception as exc:
                logger.error("alpha_vantage quote failed for %s: %s", sym, exc)
        return quotes

    @retry_with_backoff(max_retries=2, exceptions=(httpx.HTTPError, ValueError))
    def _global_quote(self, symbol: str) -> MarketQuote:
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key,
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
        gq = data.get("Global Quote") or {}
        if not gq:
            # Alpha Vantage often returns notes on rate limit
            logger.warning("alpha_vantage empty quote payload: %s", data)
            raise ValueError(f"empty Global Quote for {symbol}")
        price = float(gq.get("05. price", 0))
        change_pct_raw = gq.get("10. change percent", "0%").replace("%", "")
        return MarketQuote(
            symbol=symbol.upper(),
            price=price,
            as_of=datetime.now(timezone.utc),
            change_pct=float(change_pct_raw) if change_pct_raw else None,
            volume=float(gq.get("06. volume") or 0),
            source=self.name,
        )

    def get_history(self, symbol: str, days: int = 90) -> List[PriceBar]:
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": "compact",
            "apikey": self.api_key,
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
        series = data.get("Time Series (Daily)") or {}
        bars: List[PriceBar] = []
        for day_str, ohlcv in list(series.items())[:days]:
            bars.append(
                PriceBar(
                    symbol=symbol.upper(),
                    bar_date=datetime.strptime(day_str, "%Y-%m-%d").date(),
                    open=float(ohlcv["1. open"]),
                    high=float(ohlcv["2. high"]),
                    low=float(ohlcv["3. low"]),
                    close=float(ohlcv["4. close"]),
                    volume=float(ohlcv["5. volume"]),
                )
            )
        bars.sort(key=lambda b: b.bar_date)
        return bars
