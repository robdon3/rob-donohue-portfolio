/**
 * CLEAN-ROOM SYNTHETIC DATA ONLY
 * Persona: Jordan Lee (Demo Household) — fictional.
 * Mirrors config/synthetic_household.yaml for offline GitHub Pages.
 * Do not replace with real personal finances in this public repo.
 */
window.WORKSHEET_SEED = {
  persona_name: "Jordan Lee (Demo Household)",
  disclaimer:
    "Synthetic data for portfolio evaluation. Not real finances. Not financial advice.",
  as_of: "2026-07-18",
  accounts: [
    { id: "cash_primary", name: "Demo Checking", institution: "Northstar Bank", kind: "cash", category: "assets", balance: 4200, credit_limit: null, apr_pct: null },
    { id: "cash_reserve", name: "Demo High-Yield Savings", institution: "Northstar Bank", kind: "cash", category: "assets", balance: 6800, credit_limit: null, apr_pct: null },
    { id: "brokerage", name: "Demo Brokerage", institution: "Summit Markets", kind: "brokerage", category: "assets", balance: 0, credit_limit: null, apr_pct: null },
    { id: "retirement_401k", name: "Demo 401(k)", institution: "Summit Markets", kind: "retirement", category: "investments", balance: 0, credit_limit: null, apr_pct: null },
    { id: "ira", name: "Demo IRA", institution: "Summit Markets", kind: "retirement", category: "investments", balance: 0, credit_limit: null, apr_pct: null },
    { id: "hsa", name: "Demo HSA", institution: "HealthVault", kind: "hsa", category: "assets", balance: 2400, credit_limit: null, apr_pct: null },
    { id: "crypto", name: "Demo Crypto Wallet", institution: "OpenChain", kind: "crypto", category: "assets", balance: 0, credit_limit: null, apr_pct: null },
    { id: "points", name: "Demo Rewards Vault", institution: "Various", kind: "points", category: "assets", balance: 0, credit_limit: null, apr_pct: null },
    { id: "card_alpha", name: "Demo Card Alpha", institution: "Alpha Financial", kind: "credit", category: "liabilities", balance: 4100, credit_limit: 9000, apr_pct: 19.9 },
    { id: "card_beta", name: "Demo Card Beta", institution: "Beta Financial", kind: "credit", category: "liabilities", balance: 2850, credit_limit: 7500, apr_pct: 22.4 },
    { id: "card_gamma", name: "Demo Card Gamma", institution: "Gamma Financial", kind: "credit", category: "liabilities", balance: 960, credit_limit: 5000, apr_pct: 18.5 },
    { id: "personal_loan", name: "Demo Personal Loan", institution: "Northstar Bank", kind: "loan", category: "liabilities", balance: 7200, credit_limit: 15000, apr_pct: 9.5 },
  ],
  holdings: [
    { account_id: "cash_primary", account_name: "Demo Checking", asset: "Checking cash", ticker: "", quantity: 1, price: 4200, asset_type: "cash" },
    { account_id: "cash_reserve", account_name: "Demo High-Yield Savings", asset: "HYSA cash", ticker: "", quantity: 1, price: 6800, asset_type: "cash" },
    { account_id: "brokerage", account_name: "Demo Brokerage", asset: "Cash sweep", ticker: "SWEEP", quantity: 2100, price: 1, asset_type: "cash" },
    { account_id: "brokerage", account_name: "Demo Brokerage", asset: "Broad market ETF", ticker: "VTI", quantity: 45, price: 255, asset_type: "stock" },
    { account_id: "brokerage", account_name: "Demo Brokerage", asset: "Mega-cap tech", ticker: "AAPL", quantity: 12, price: 188, asset_type: "stock" },
    { account_id: "brokerage", account_name: "Demo Brokerage", asset: "Software", ticker: "MSFT", quantity: 8, price: 415, asset_type: "stock" },
    { account_id: "retirement_401k", account_name: "Demo 401(k)", asset: "Target-date fund", ticker: "TD2060", quantity: 320, price: 48.5, asset_type: "retirement" },
    { account_id: "ira", account_name: "Demo IRA", asset: "Total stock index", ticker: "VTSAX", quantity: 85, price: 130, asset_type: "retirement" },
    { account_id: "hsa", account_name: "Demo HSA", asset: "HSA cash", ticker: "", quantity: 1, price: 2400, asset_type: "health_savings" },
    { account_id: "crypto", account_name: "Demo Crypto Wallet", asset: "Ethereum", ticker: "ETH", quantity: 0.35, price: 3200, asset_type: "crypto" },
    { account_id: "crypto", account_name: "Demo Crypto Wallet", asset: "Bitcoin", ticker: "BTC", quantity: 0.02, price: 64000, asset_type: "crypto" },
    { account_id: "points", account_name: "Demo Rewards Vault", asset: "Airline miles (est. $)", ticker: "", quantity: 1, price: 480, asset_type: "points" },
    { account_id: "points", account_name: "Demo Rewards Vault", asset: "Hotel points (est. $)", ticker: "", quantity: 1, price: 220, asset_type: "points" },
    { account_id: "card_alpha", account_name: "Demo Card Alpha", asset: "Revolving balance", ticker: "", quantity: 1, price: 4100, asset_type: "credit_debt" },
    { account_id: "card_beta", account_name: "Demo Card Beta", asset: "Revolving balance", ticker: "", quantity: 1, price: 2850, asset_type: "credit_debt" },
    { account_id: "card_gamma", account_name: "Demo Card Gamma", asset: "Revolving balance", ticker: "", quantity: 1, price: 960, asset_type: "credit_debt" },
    { account_id: "personal_loan", account_name: "Demo Personal Loan", asset: "Loan principal", ticker: "", quantity: 1, price: 7200, asset_type: "loan_debt" },
  ],
  snapshots: [
    { as_of: "2024-06-24", assets: 28000, liabilities: -42000, investments: 22000 },
    { as_of: "2024-12-31", assets: 31000, liabilities: -38000, investments: 28000 },
    { as_of: "2025-06-15", assets: 35000, liabilities: -34000, investments: 36000 },
    { as_of: "2025-12-31", assets: 38000, liabilities: -30000, investments: 42000 },
    { as_of: "2026-03-01", assets: 40000, liabilities: -28000, investments: 48000 },
    { as_of: "2026-06-01", assets: 43000, liabilities: -26000, investments: 52000 },
    { as_of: "2026-07-10", assets: 45500, liabilities: -25500, investments: 54500 },
    { as_of: "2026-07-17", assets: 44800, liabilities: -25100, investments: 53800 },
  ],
  runway: {
    monthly_expenses: 4200,
    months_target: 6,
    fund_account_ids: ["cash_reserve", "cash_primary"],
  },
  cashflow: {
    net_income_annual: 96000,
    cadence: "biweekly",
    waterfall: [
      { name: "Housing", fraction: 0.28 },
      { name: "Essentials", fraction: 0.18 },
      { name: "Debt payments", fraction: 0.22 },
      { name: "Investing", fraction: 0.15 },
      { name: "Buffer / fun", fraction: 0.1 },
      { name: "Emergency fund top-up", fraction: 0.07 },
    ],
    scenarios: [
      { name: "baseline", income_multiplier: 1, debt_extra: 0 },
      { name: "aggressive_debt", income_multiplier: 1, debt_extra: 400 },
      { name: "reduced_income", income_multiplier: 0.85, debt_extra: 0 },
    ],
  },
  ops: {
    notes: "Stay the course. Synthetic market directive for demo only.",
    market_directive: "Monitor cycle; rebalance quarterly. Not advice.",
    card_of_day: {
      Monday: "card_gamma",
      Tuesday: "card_alpha",
      Wednesday: "card_beta",
      Thursday: "card_alpha",
      Friday: "card_beta",
      Saturday: "card_gamma",
      Sunday: "card_gamma",
    },
  },
};
