"""
Worksheet OS orchestrator — composes ledger, debt, snapshots, runway, cashflow.

Single entrypoint used by CLI and JSON export for the browser demo seed.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from ..cashflow.waterfall import build_cashflow, run_scenarios
from ..debt.stack import build_debt_stack
from ..ledger.core import load_ledger_from_config
from ..models.worksheet import WorksheetBundle
from ..runway.fund import compute_runway
from ..snapshots.history import SnapshotStore, cockpit_from_history
from ..utils.logging_setup import get_logger

logger = get_logger(__name__)

PKG_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SYNTHETIC = PKG_ROOT / "config" / "synthetic_household.yaml"


def _load_yaml(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml

        return yaml.safe_load(text) or {}
    except ImportError as exc:
        raise ImportError(
            "PyYAML is required for worksheet config. pip install pyyaml"
        ) from exc


def load_synthetic_config(path: Optional[Path] = None) -> Dict[str, Any]:
    cfg_path = path or DEFAULT_SYNTHETIC
    logger.info("loading synthetic household config %s", cfg_path)
    return _load_yaml(cfg_path)


def run_worksheet(
    config: Optional[Dict[str, Any]] = None,
    config_path: Optional[Path] = None,
    as_of: Optional[date] = None,
) -> WorksheetBundle:
    """Build full multi-view worksheet bundle from synthetic (or provided) config."""
    cfg = config if config is not None else load_synthetic_config(config_path)
    as_of = as_of or date.today()
    persona = cfg.get("persona", {})

    ledger = load_ledger_from_config(cfg)
    buckets = ledger.bucket_totals()
    home = ledger.home_buckets()

    store = SnapshotStore.from_config(cfg.get("snapshots", []))
    cockpit = cockpit_from_history(store, buckets, as_of=as_of)

    debt = build_debt_stack(ledger, as_of=as_of)
    runway = compute_runway(ledger, cfg.get("runway", {}))
    cashflow = build_cashflow(cfg.get("cashflow", {}))
    scenarios = run_scenarios(cfg.get("cashflow", {}))

    ops = cfg.get("ops_policy", {})
    # Resolve card-of-day name for weekday
    weekday = as_of.strftime("%A")
    card_id = (ops.get("card_of_day") or {}).get(weekday)
    card_name = None
    if card_id and card_id in ledger.accounts:
        card_name = ledger.accounts[card_id].name

    accounts_df = ledger.accounts_frame()
    holdings_df = ledger.holdings_frame()

    def _records(df):
        if df is None or df.empty:
            return []
        return df.where(df.notna(), None).to_dict(orient="records")

    bundle = WorksheetBundle(
        persona_name=ledger.persona_name,
        disclaimer=ledger.disclaimer,
        generated_at=datetime.now(timezone.utc),
        cockpit=cockpit,
        accounts=_records(accounts_df),
        holdings=_records(holdings_df),
        debt_stack=debt,
        runway=runway,
        cashflow=cashflow,
        scenarios=scenarios,
        ops={
            "notes": ops.get("notes", ""),
            "market_directive": ops.get("market_directive", ""),
            "card_of_day_id": card_id,
            "card_of_day_name": card_name,
            "weekday": weekday,
        },
        buckets={**buckets, "home": home},
    )
    logger.info(
        "worksheet complete persona=%s NW=%.2f holdings=%s",
        bundle.persona_name,
        cockpit.net_worth,
        len(bundle.holdings),
    )
    return bundle


def bundle_to_jsonable(bundle: WorksheetBundle) -> dict:
    return bundle.model_dump(mode="json")
