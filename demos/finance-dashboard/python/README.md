# Personal Finance Dashboard — Python Core

API-connected portfolio demo: **adapters → ETL → analytics → CLI**.

Designed as an original, shareable framework you can re-point at real APIs and holdings.

## Architecture (short)

```
config/settings.yaml ──► main.py
                           │
                     get_market_client()
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
           mock      yfinance    alpha_vantage
              └────────────┬────────────┘
                           ▼
                  FinanceETLPipeline
                    quotes / history
                    positions join
                           ▼
                  PortfolioAnalytics
                 snapshot · allocation
                 projection · metrics
```

### Design decisions

| Choice | Why |
|--------|-----|
| **Adapter interface** (`MarketDataClient`) | Swap providers without touching analytics |
| **Mock default** | Offline demos, CI, interviews — always works |
| **Pydantic domain models** | Stable contracts across layers |
| **Pure analytics** | Testable without network |
| **Structured logging + retries** | Production-shaped operability |
| **Config YAML + env** | Vibe-friendly: edit holdings, not code |

### Trade-offs

- **yfinance**: convenient, no key — not a production SLA feed  
- **Alpha Vantage free tier**: hard rate limits — cache and mock for bulk demos  
- **Projections**: simple compound model — educational, not advice  
- **No auth/multi-tenant**: portfolio is local config by design  

## Quick start

```bash
cd demos/finance-dashboard/python
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Offline demo (default)
python -m src.main --demo

# Live Yahoo data (no API key)
FINANCE_PROVIDER=yfinance python -m src.main --demo

# Alpha Vantage
cp .env.example .env
# set ALPHA_VANTAGE_API_KEY=...
FINANCE_PROVIDER=alpha_vantage python -m src.main --demo

# Export snapshot
python -m src.main --demo --export-json data/output/snapshot.json
```

## Tests

```bash
pytest -q
```

## Extension points (vibe here)

1. **New API** — implement `MarketDataClient`, register in `clients/factory.py`  
2. **Holdings** — edit `config/settings.yaml`  
3. **Metrics** — add methods on `PortfolioAnalytics`  
4. **UI** — call `FinanceETLPipeline.run_portfolio_etl` from Streamlit/FastAPI  
5. **Real tracking** — replace mock cost basis with brokerage CSV import adapter  

## Layout

```
python/
├── config/settings.yaml
├── src/
│   ├── main.py              # CLI
│   ├── config_loader.py
│   ├── clients/             # adapters
│   ├── etl/                 # normalize + join
│   ├── analytics/           # portfolio math
│   ├── models/              # pydantic contracts
│   └── utils/               # logging, retry
├── tests/
├── data/                    # sample + output (gitignored cache)
├── requirements.txt
└── .env.example
```

## Disclaimer

Not financial advice. Market data may be delayed or synthetic. Demo for architecture evaluation only.
