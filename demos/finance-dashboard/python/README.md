# Personal finance control system — Python

Synthetic reconstruction of a purpose-built personal workbook.

- **Areas with jobs** (control, journal, holdings, debt, payments testground, paycheck)
- **Journal upsert** — same rules as Sheets Apps Script `copyDataToJournal`
- **Payments testground** — try strategies without touching the live ledger
- Optional **market-demo** for mark-to-market adapters

## Run

```bash
python -m src.main --worksheet
python -m src.main --worksheet --export-json data/output/worksheet.json
pytest -q
```

## Journal rules (method)

1. Read control totals for the day  
2. Match on date only (ignore formula columns)  
3. Same day → overwrite  
4. New day → append  

See `automation/copyDataToJournal.gs.js` and `src/journal/daily.py`.

## Layout

```
src/
  ledger/      accounts + holdings
  journal/     daily upsert
  debt/        stack + clocks
  payments/    testground strategies
  snapshots/   ATH/ATL/YTD
  runway/      expense fund
  cashflow/    paycheck waterfall
  worksheet/   engine
  clients/     optional market adapters
```

## Disclaimer

Synthetic only. Not financial advice. Not real personal data.
