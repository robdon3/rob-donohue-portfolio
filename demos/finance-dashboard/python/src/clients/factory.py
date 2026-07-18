"""Provider factory — single place to swap data sources."""

from __future__ import annotations

import os

from ..utils.logging_setup import get_logger
from .alpha_vantage_client import AlphaVantageClient
from .base import MarketDataClient
from .mock_client import MockMarketClient
from .yfinance_client import YFinanceClient

logger = get_logger(__name__)


def get_market_client(provider: str | None = None) -> MarketDataClient:
    """
    Resolve market data client from env or explicit name.

    Supported: mock | yfinance | alpha_vantage
    """
    name = (provider or os.getenv("FINANCE_PROVIDER", "mock")).strip().lower()
    logger.info("resolving market client provider=%s", name)

    if name in ("mock", "demo"):
        return MockMarketClient()
    if name == "yfinance":
        return YFinanceClient()
    if name in ("alpha_vantage", "alphavantage", "av"):
        return AlphaVantageClient()

    raise ValueError(
        f"Unknown FINANCE_PROVIDER '{name}'. "
        "Use mock | yfinance | alpha_vantage"
    )
