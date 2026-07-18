# Financial Worksheet OS

| Artifact | Link |
|----------|------|
| **Live demo (Pages)** | [index.html](./index.html) |
| **Architecture write-up** | [../../projects/finance-dashboard.html](../../projects/finance-dashboard.html) |
| **Python package** | [python/](./python/) |
| **Synthetic config** | [python/config/synthetic_household.yaml](./python/config/synthetic_household.yaml) |

## Clean-room notice

Public demo uses a **fictional household** (Jordan Lee).  
Do not commit real balances, payroll, or institution fingerprints to this repo.

## Views

Cockpit · Accounts · Holdings · Debt stack · Paycheck · Phone

## Quick start

```bash
cd python && pip install -r requirements.txt
python -m src.main --worksheet && pytest -q
```
