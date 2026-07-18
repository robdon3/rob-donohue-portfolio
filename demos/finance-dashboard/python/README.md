# Financial Worksheet OS — Python Core

Clean-room multi-view personal finance system for architecture demos.

**Synthetic data only** (`config/synthetic_household.yaml`).  
No real balances, institutions, or PII belong in this package for public use.

## What it is

A modular reimplementation of a “worksheet-class” finance OS:

| View | Module |
|------|--------|
| Cockpit KPIs (NW, ATH/ATL, YTD, A/D) | `snapshots/` + `ledger/` |
| Accounts ledger | `ledger/` |
| Holdings grid | `ledger/` |
| Debt stack | `debt/` |
| Expense runway | `runway/` |
| Paycheck waterfall + scenarios | `cashflow/` |
| Composition root | `worksheet/` |
| Optional market mark-to-market | `clients/` + `--market-demo` |

## Quick start

```bash
cd demos/finance-dashboard/python
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Default: full worksheet OS (synthetic)
python -m src.main --worksheet
python -m src.main --worksheet --export-json data/output/worksheet.json

# Original API market slice
python -m src.main --market-demo
FINANCE_PROVIDER=yfinance python -m src.main --market-demo

pytest -q
```

## Architecture

```
synthetic_household.yaml
        │
        ▼
 worksheet.engine.run_worksheet()
        │
        ├─► ledger        accounts + holdings → buckets
        ├─► debt          utilization, % stack, payoff clocks
        ├─► snapshots     ATH / ATL / YTD / daily Δ
        ├─► runway        N-month expense fund
        └─► cashflow      biweekly waterfall + scenarios
                │
                ▼
         WorksheetBundle → CLI / JSON / browser seed
```

### Design decisions

| Choice | Why |
|--------|-----|
| Dual grain (accounts + holdings) | Matches real power-user worksheets |
| Snapshots as append-only series | ATH/ATL integrity vs overwriting cells |
| Liabilities first-class | Debt is not “negative stock” |
| Synthetic default | Safe public portfolio artifact |
| Pure-ish modules | Unit test without network |

### Extension points

1. Swap `synthetic_household.yaml` numbers (keep fictional).
2. Import CSV → build the same config dict → `run_worksheet(config=...)`.
3. Streamlit tabs over `WorksheetBundle`.
4. Mark-to-market: price stock/crypto holdings via `clients/` before rollup.

## Layout

```
python/
├── config/
│   ├── synthetic_household.yaml   # clean-room persona
│   └── settings.yaml              # market-demo portfolio
├── src/
│   ├── main.py
│   ├── worksheet/                 # orchestrator
│   ├── ledger/
│   ├── debt/
│   ├── snapshots/
│   ├── runway/
│   ├── cashflow/
│   ├── clients/                   # market adapters
│   ├── etl/ analytics/ models/    # market-demo spine
│   └── utils/
└── tests/
```

## Disclaimer

Not financial advice. Synthetic demo for systems architecture evaluation.
