"""yfinance adapter — free, no API key. Swap in via FINANCE_PROVIDER=yfinance."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Sequence

from ..models.domain import MarketQuote, PriceBar
from ..utils.logging_setup import get_logger
from ..utils.retry import retry_with_backoff
from .base import MarketDataClient

logger = get_logger(__name__)


class YFinanceClient(MarketDataClient):
    """
    Yahoo Finance via yfinance.

    Trade-off: convenient for demos; not a contractual SLA for production.
    For production market data, prefer licensed feeds with SLAs.
    """

    name = "yfinance"

    def __init__(self) -> None:
        try:
            import yfinance  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "yfinance is required for this provider. "
                "pip install yfinance  OR use FINANCE_PROVIDER=mock"
            ) from exc

    def get_quotes(self, symbols: Sequence[str]) -> List[MarketQuote]:
        import yfinance as yf

        quotes: List[MarketQuote] = []
        for sym in symbols:
            try:
                quotes.append(self._quote_one(yf, sym))
            except Exception as exc:  # isolate per-symbol failure
                logger.error("yfinance quote failed for %s: %s", sym, exc)
        return quotes

    @retry_with_backoff(max_retries=2, exceptions=(Exception,))
    def _quote_one(self, yf, symbol: str) -> MarketQuote:
        t = yf.Ticker(symbol)
        info = {}
        try:
            # fast_info is lighter than full info where available
            fast = getattr(t, "fast_info", None)
            if fast:
                price = float(fast.get("last_price") or fast.get("lastPrice") or 0)
                prev = float(fast.get("previous_close") or fast.get("previousClose") or price)
            else:
                hist = t.history(period="5d")
                if hist.empty:
                    raise ValueError(f"no history for {symbol}")
                price = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price
                info = {}
            change = ((price - prev) / prev) * 100 if prev else None
            return MarketQuote(
                symbol=symbol.upper(),
                price=price,
                as_of=datetime.now(timezone.utc),
                change_pct=round(change, 3) if change is not None else None,
                source=self.name,
            )
        finally:
            del info

    def get_history(self, symbol: str, days: int = 90) -> List[PriceBar]:
        import yfinance as yf

        period = "3mo" if days <= 90 else "1y"
        t = yf.Ticker(symbol)
        hist = t.history(period=period)
        bars: List[PriceBar] = []
        if hist is None or hist.empty:
            logger.warning("yfinance empty history for %s", symbol)
            return bars
        for idx, row in hist.tail(days).iterrows():
            bars.append(
                PriceBar(
                    symbol=symbol.upper(),
                    bar_date=idx.date() if hasattr(idx, "date") else idx,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row.get("Volume", 0) or 0),
                )
            )
        return bars
