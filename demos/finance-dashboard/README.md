# Personal Finance Dashboard

| Artifact | Link |
|----------|------|
| **Live demo (Pages)** | [index.html](./index.html) |
| **Architecture write-up** | [../../projects/finance-dashboard.html](../../projects/finance-dashboard.html) |
| **Python package** | [python/](./python/) |

## What it demonstrates

- API adapter pattern (mock / yfinance / Alpha Vantage)
- ETL normalize + holdings join
- Portfolio analytics (P&L, allocation, projection, rough risk)
- Production-vibe: typing, logging, retries, config, tests
- GitHub Pages–friendly browser demo (mock provider)

## Quick links for reviewers

```bash
cd python && pip install -r requirements.txt && python -m src.main --demo && pytest -q
```
