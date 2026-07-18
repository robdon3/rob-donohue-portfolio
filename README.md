# Rob Donohue — Systems Architecture Portfolio

**Original demo frameworks** for AI infrastructure, solution architecture, and defense-tech roles.

> First-principles architecture. Modular systems that stand independently. LLMs as implementation accelerators—not substitutes for design.

🌐 **Live site:** [https://robdon3.github.io/rob-donohue-portfolio/](https://robdon3.github.io/rob-donohue-portfolio/)

---

## Who This Is For

Hiring managers and technical leaders evaluating systems architecture depth through **shareable demos**—not client IP. Each project emphasizes:

- **Data flow & modularity** — clear boundaries, swappable adapters
- **API-connected Python** — integrations, ETL, error resilience, logging
- **Production-vibe code** — typing, config, tests, extension points
- **Architecture narratives** — trade-offs, scalability, “how I architected this”

## Portfolio Sections

| Section | Purpose |
|---------|---------|
| Hero / About | Background: MBSE, data/ETL, AI/automation, TS-cleared environments |
| Skills / Stack | Technical surface area with architecture focus |
| Demo Projects | 4–6 original frameworks (runnable + documented) |
| Philosophy | Fountainhead-inspired first principles |
| Contact | Reach out / download full portfolio PDF |

## Demo Frameworks

| # | Project | Status | Focus |
|---|---------|--------|--------|
| 1 | [Finance control system](demos/finance-dashboard/) | ✅ Live | Purpose-built areas, Journal upsert, payments testground (synthetic) |
| 2 | PDF / Document Reconciliation | 🔜 Next | Parse → extract → reconcile (PyMuPDF, pandas) |
| 3 | Automation Pipeline Framework | Planned | Multi-source aggregator, ETL, logging |
| 4 | Advanced Financial Analyzer | Planned | Sheets-class modeling in Python |
| 5 | Lightweight RAG Mock | Planned | Retrieval patterns for AI infra roles |
| 6 | Job Tracker (API) | Planned | Multi-API orchestration |

### Personal finance control system (ready)

Purpose-built workbook structure (synthetic numbers): control surface, Journal automation,
debt, payments testground, paycheck. Not real personal data.

```bash
cd demos/finance-dashboard/python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.main --worksheet
python -m src.main --market-demo   # optional market adapters
```

- **Live demo:** [demos/finance-dashboard/](demos/finance-dashboard/)
- **How it's built:** [projects/finance-dashboard.html](projects/finance-dashboard.html)

## Site Stack

- Static **HTML / CSS / JS** (no build step) — GitHub Pages friendly
- Dark-first tech aesthetic, responsive, accessible contrast
- Mermaid diagrams for architecture views
- Chart.js for live demo visualizations

## Local Development

```bash
git clone https://github.com/robdon3/rob-donohue-portfolio.git
cd rob-donohue-portfolio
# Any static server works:
python3 -m http.server 8080
# open http://localhost:8080
```

## Design Philosophy (short)

1. **Independence** — each module has a single job and clear contract  
2. **First principles** — solve the data/control problem before picking frameworks  
3. **Resilience** — retries, timeouts, degraded modes, structured logs  
4. **Extensibility** — swap mock ↔ live APIs without rewriting core logic  
5. **LLM as force multiplier** — architecture owns the system; tools accelerate code  

## License

Demo code is provided for portfolio evaluation and educational use.  
© Rob Donohue — all rights reserved unless otherwise noted in a subfolder.
