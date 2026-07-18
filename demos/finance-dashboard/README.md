# Personal finance control system (demo)

| Artifact | Link |
|----------|------|
| **Live demo** | [index.html](./index.html) |
| **How it's built** | [../../projects/finance-dashboard.html](../../projects/finance-dashboard.html) |
| **Python** | [python/](./python/) |
| **Apps Script pattern** | [python/automation/copyDataToJournal.gs.js](./python/automation/copyDataToJournal.gs.js) |

## What this is

Purpose-built areas with jobs: control surface, Journal (upsert by date), holdings, debt,
**payments testground**, paycheck, phone view.

Public numbers are **synthetic**. Real workbook stays private.

## Run

```bash
cd python && pip install -r requirements.txt
python -m src.main --worksheet && pytest -q
```
