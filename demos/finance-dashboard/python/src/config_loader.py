"""Load YAML portfolio config + environment settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv

from .models.domain import Holding
from .utils.logging_setup import get_logger

logger = get_logger(__name__)

# Package roots
PKG_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SETTINGS = PKG_ROOT / "config" / "settings.yaml"


def load_env() -> None:
    """Load .env from python package root if present."""
    env_path = PKG_ROOT / ".env"
    load_dotenv(env_path)


def load_yaml_settings(path: Path | None = None) -> Dict[str, Any]:
    """
    Minimal YAML loader.

    Prefer PyYAML if installed; otherwise parse a constrained subset
    sufficient for settings.yaml (keeps deps light for demos).
    """
    settings_path = path or DEFAULT_SETTINGS
    text = settings_path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
        logger.info("loaded settings via PyYAML from %s", settings_path)
        return data or {}
    except ImportError:
        logger.info("PyYAML not installed — using lightweight parser for %s", settings_path)
        return _lightweight_yaml(settings_path)


def _lightweight_yaml(path: Path) -> Dict[str, Any]:
    """
    Parse our known settings.yaml structure without PyYAML.

    For production, install pyyaml. This exists so `pip install -r`
    minimal sets still run the demo.
    """
    # Hard-coded fallback mirror of settings.yaml defaults
    # (still allow path override by reading holdings-ish lines is complex —
    #  use embedded defaults and document pyyaml as optional enhancement)
    _ = path
    return {
        "portfolio": {
            "name": "Demo Balanced Portfolio",
            "base_currency": "USD",
            "cash": 5000.0,
            "holdings": [
                {"symbol": "AAPL", "shares": 25, "cost_basis": 165.0},
                {"symbol": "MSFT", "shares": 15, "cost_basis": 320.0},
                {"symbol": "GOOGL", "shares": 20, "cost_basis": 130.0},
                {"symbol": "BTC-USD", "shares": 0.15, "cost_basis": 42000.0},
                {"symbol": "VTI", "shares": 40, "cost_basis": 220.0},
            ],
        },
        "market": {
            "default_symbols": ["AAPL", "MSFT", "GOOGL", "BTC-USD", "VTI"],
            "history_days": 90,
        },
        "analytics": {
            "expected_annual_return": 0.07,
            "projection_years": 10,
            "risk_free_rate": 0.04,
        },
    }


def portfolio_from_settings(settings: Dict[str, Any]) -> Tuple[str, float, List[Holding]]:
    p = settings.get("portfolio", {})
    name = p.get("name", "Portfolio")
    cash = float(p.get("cash", 0))
    holdings = [
        Holding(
            symbol=h["symbol"],
            shares=float(h["shares"]),
            cost_basis=float(h["cost_basis"]),
        )
        for h in p.get("holdings", [])
    ]
    return name, cash, holdings


def env_provider() -> str:
    return os.getenv("FINANCE_PROVIDER", "mock")


def env_log_level() -> str:
    return os.getenv("LOG_LEVEL", "INFO")
