# Rob Donohue — Systems Architecture Portfolio

A static site for original systems demos, plus one runnable finance worksheet. The numbers in that demo are synthetic. This repository does not contain client work.

**Live site:** [https://robdon3.github.io/rob-donohue-portfolio/](https://robdon3.github.io/rob-donohue-portfolio/)

## What it is

A GitHub Pages site (HTML, CSS, and JavaScript, no build step) with one complete demo: a personal-finance control worksheet. Other project slots described on the site are not implemented in this repo.

## Problem

Show module boundaries, adapters, and data flow in something a reviewer can open, without real personal or client data.

## Approach

```text
Browser demo (demos/finance-dashboard/)
  worksheet-data.js → demo.js views
  (control, accounts, holdings, debt, payments,
   journal, paycheck, phone)

Python package (demos/finance-dashboard/python/)
  --worksheet
    config/synthetic_household.yaml
          → worksheet engine
          → ledger, journal upsert, debt stack,
            payments testground, cashflow, runway

  --market-demo (separate path; not required for the worksheet)
    config/settings.yaml
          → market clients (mock, yfinance, Alpha Vantage)
```

`--worksheet` reads only the synthetic household file. `--market-demo` is a separate path and is not required for the worksheet. The default market provider is an offline mock; yfinance and Alpha Vantage need a network.

## Run

Site:

```bash
python3 -m http.server 8080
# http://localhost:8080
# worksheet UI: http://localhost:8080/demos/finance-dashboard/
```

Python worksheet (Python 3.10+):

```bash
cd demos/finance-dashboard/python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.main --worksheet
pytest -q
```

Optional market demo (Alpha Vantage needs `ALPHA_VANTAGE_API_KEY` in a local `.env`, which is not committed):

```bash
python -m src.main --market-demo
FINANCE_PROVIDER=yfinance python -m src.main --market-demo
```

Narrative of the worksheet design: [projects/finance-dashboard.html](projects/finance-dashboard.html).

## Tech

HTML, CSS, JavaScript, and Chart.js on the site. Python, pandas, pydantic, httpx, PyYAML, Rich, yfinance, and pytest in the worksheet package.
