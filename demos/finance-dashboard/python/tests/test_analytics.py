"""Unit tests — pure analytics (no network)."""

from __future__ import annotations

import pandas as pd

from src.analytics.portfolio import PortfolioAnalytics
from src.clients.mock_client import MockMarketClient
from src.etl.pipeline import FinanceETLPipeline
from src.models.domain import Holding


def test_mock_quotes_nonempty():
    client = MockMarketClient()
    quotes = client.get_quotes(["AAPL", "MSFT"])
    assert len(quotes) == 2
    assert quotes[0].price > 0


def test_etl_positions_and_snapshot():
    client = MockMarketClient()
    pipe = FinanceETLPipeline(client)
    holdings = [
        Holding(symbol="AAPL", shares=10, cost_basis=100),
        Holding(symbol="MSFT", shares=5, cost_basis=200),
    ]
    result = pipe.run_portfolio_etl(holdings, history_days=30)
    assert not result["positions"].empty
    assert "market_value" in result["positions"].columns

    analytics = PortfolioAnalytics()
    snap = analytics.snapshot("Test", result["positions"], cash=1000)
    assert snap.total_market_value > 1000
    assert len(snap.positions) == 2


def test_projection_grows():
    analytics = PortfolioAnalytics(expected_annual_return=0.10, projection_years=5)
    df = analytics.project_growth(10_000)
    assert df.iloc[-1]["value"] > 10_000


def test_history_returns():
    client = MockMarketClient()
    bars = client.get_history("AAPL", days=40)
    df = FinanceETLPipeline.history_to_frame(bars)
    analytics = PortfolioAnalytics()
    rets = analytics.history_returns(df)
    assert "daily_return" in rets.columns
    metrics = analytics.summary_metrics(df)
    assert "ann_vol_est" in metrics
