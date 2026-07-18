/**
 * Financial Worksheet OS — browser engine (clean-room synthetic).
 * Mirrors Python: ledger → debt → snapshots → runway → cashflow.
 */
(function () {
  "use strict";

  const LIABILITY_TYPES = new Set(["credit_debt", "loan_debt"]);
  let debtChart = null;
  let sleeveChart = null;
  let nwChart = null;

  function money(n) {
    if (n == null || Number.isNaN(n)) return "—";
    const sign = n < 0 ? "-" : "";
    return sign + "$" + Math.abs(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function pct(n) {
    if (n == null || Number.isNaN(n)) return "—";
    return n.toFixed(1) + "%";
  }

  function log(msg, cls) {
    const el = document.getElementById("demo-log");
    if (!el) return;
    const line = document.createElement("div");
    line.className = cls || "info";
    line.textContent = new Date().toISOString().slice(11, 19) + " | " + msg;
    el.prepend(line);
  }

  function valueOf(h) {
    return h.quantity * h.price;
  }

  function computeBuckets(holdings) {
    let assets = 0, investments = 0, liabilities = 0;
    const home = {
      cash: 0, stocks: 0, retirement: 0, crypto: 0, points: 0,
      health_savings: 0, credit_debt: 0, loan_debt: 0,
    };
    for (const h of holdings) {
      const v = valueOf(h);
      if (LIABILITY_TYPES.has(h.asset_type)) {
        liabilities -= Math.abs(v);
        home[h.asset_type] = (home[h.asset_type] || 0) + Math.abs(v);
      } else if (h.asset_type === "retirement" || h.asset_type === "stock") {
        investments += v;
        if (h.asset_type === "retirement") home.retirement += v;
        else home.stocks += v;
      } else {
        assets += v;
        if (home[h.asset_type] != null) home[h.asset_type] += v;
      }
    }
    return {
      assets, investments, liabilities,
      net_worth: assets + investments + liabilities,
      assets_plus_investments: assets + investments,
      home,
    };
  }

  function rollupAccounts(seed, holdings) {
    return seed.accounts.map((a) => {
      const lines = holdings.filter((h) => h.account_id === a.id);
      const balance = lines.reduce((s, h) => s + valueOf(h), 0);
      const util =
        a.credit_limit && a.kind === "credit"
          ? (balance / a.credit_limit) * 100
          : null;
      return { ...a, balance, utilization_pct: util };
    });
  }

  function debtStack(accounts, holdings) {
    const facilities = [];
    let total = 0;
    for (const h of holdings) {
      if (!LIABILITY_TYPES.has(h.asset_type)) continue;
      const bal = Math.abs(valueOf(h));
      total += bal;
      const acct = accounts.find((a) => a.id === h.account_id) || {};
      facilities.push({
        account_id: h.account_id,
        name: acct.name || h.account_id,
        balance: bal,
        limit: acct.credit_limit,
        apr_pct: acct.apr_pct,
        utilization_pct:
          acct.credit_limit ? (bal / acct.credit_limit) * 100 : null,
      });
    }
    facilities.forEach((f) => {
      f.pct_of_debt = total ? (f.balance / total) * 100 : 0;
      // rough payoff months
      const r = ((f.apr_pct || 0) / 100) / 12;
      const pay = Math.max(f.balance * 0.02, 50);
      if (r <= 0) f.payoff_months = f.balance / pay;
      else if (pay <= r * f.balance) f.payoff_months = null;
      else f.payoff_months = Math.log(pay / (pay - r * f.balance)) / Math.log(1 + r);
    });
    facilities.sort((a, b) => b.balance - a.balance);
    return facilities;
  }

  function cockpit(buckets, snapshots, asOf) {
    const live = {
      as_of: asOf,
      assets: buckets.assets,
      liabilities: buckets.liabilities,
      investments: buckets.investments,
      net_worth: buckets.net_worth,
    };
    const series = snapshots
      .map((s) => ({
        ...s,
        net_worth: s.assets + s.liabilities + s.investments,
      }))
      .concat([live]);
    series.sort((a, b) => a.as_of.localeCompare(b.as_of));

    const ath = series.reduce((b, s) => (s.net_worth > b.net_worth ? s : b));
    const atl = series.reduce((b, s) => (s.net_worth < b.net_worth ? s : b));
    const debts = series.map((s) => s.liabilities);
    const debtHi = Math.min(...debts);
    const debtLo = Math.max(...debts);
    const year = asOf.slice(0, 4);
    const prior = [...series].reverse().find((s) => s.as_of < year + "-01-01") || series[0];
    const prev = series[series.length - 2];
    const ad = buckets.liabilities
      ? buckets.assets_plus_investments / Math.abs(buckets.liabilities)
      : null;

    return {
      live,
      series,
      ath,
      atl,
      debtHi,
      debtLo,
      ytd: live.net_worth - prior.net_worth,
      daily: prev ? live.net_worth - prev.net_worth : 0,
      ad_ratio: ad,
    };
  }

  function runway(seed, holdings) {
    const monthly = seed.runway.monthly_expenses;
    const target = monthly * seed.runway.months_target;
    const ids = new Set(seed.runway.fund_account_ids);
    const current = holdings
      .filter((h) => ids.has(h.account_id) && !LIABILITY_TYPES.has(h.asset_type))
      .reduce((s, h) => s + valueOf(h), 0);
    const deficit = Math.max(target - current, 0);
    return {
      monthly,
      months_target: seed.runway.months_target,
      target,
      current,
      months_covered: monthly ? current / monthly : 0,
      deficit,
      catchup_monthly: deficit / 12,
      catchup_biweekly: deficit / 24,
    };
  }

  function cashflow(seed, scenarioName) {
    const sc =
      seed.cashflow.scenarios.find((s) => s.name === scenarioName) ||
      seed.cashflow.scenarios[0];
    const annual = seed.cashflow.net_income_annual * (sc.income_multiplier || 1);
    const paycheck = annual / 26;
    const waterfall = seed.cashflow.waterfall.map((b) => ({
      name: b.name,
      fraction: b.fraction,
      amount: paycheck * b.fraction,
    }));
    if (sc.debt_extra) {
      const debt = waterfall.find((b) => /debt/i.test(b.name));
      if (debt) debt.amount += sc.debt_extra;
      else waterfall.push({ name: "Extra debt", fraction: 0, amount: sc.debt_extra });
    }
    return { scenario: sc.name, annual, paycheck, waterfall };
  }

  function cardOfDay(seed, asOf) {
    const d = new Date(asOf + "T12:00:00");
    const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    const weekday = days[d.getDay()];
    const id = seed.ops.card_of_day[weekday];
    const acct = seed.accounts.find((a) => a.id === id);
    return { weekday, id, name: acct ? acct.name : id };
  }

  function setText(id, text, cls) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = text;
    if (cls) el.className = "kpi-value " + cls;
  }

  function renderCockpit(state) {
    const { buckets, cp, rw, card, seed } = state;
    setText("kpi-nw", money(buckets.net_worth), buckets.net_worth >= 0 ? "up" : "down");
    setText("kpi-assets", money(buckets.assets));
    setText("kpi-investments", money(buckets.investments));
    setText("kpi-liabilities", money(buckets.liabilities), "down");
    setText("kpi-ad", cp.ad_ratio != null ? cp.ad_ratio.toFixed(2) : "—");
    setText("kpi-ytd", money(cp.ytd), cp.ytd >= 0 ? "up" : "down");
    setText("kpi-daily", money(cp.daily), cp.daily >= 0 ? "up" : "down");
    setText("kpi-ath", money(cp.ath.net_worth) + " · " + cp.ath.as_of);
    setText("kpi-atl", money(cp.atl.net_worth) + " · " + cp.atl.as_of);
    setText("kpi-runway", rw.months_covered.toFixed(1) + " / " + rw.months_target + " mo");
    setText("kpi-card", card.name || "—");

    const dir = document.getElementById("ops-directive");
    if (dir) dir.textContent = seed.ops.market_directive + " — " + seed.ops.notes;

    const rwNote = document.getElementById("runway-note");
    if (rwNote) {
      rwNote.textContent =
        `Expense fund ${money(rw.current)} / target ${money(rw.target)} · ` +
        `deficit ${money(rw.deficit)} · catch-up ${money(rw.catchup_monthly)}/mo`;
    }
  }

  function fillTable(tbodySelector, rowsHtml) {
    const tbody = document.querySelector(tbodySelector);
    if (tbody) tbody.innerHTML = rowsHtml;
  }

  function renderAccounts(accounts) {
    fillTable(
      "#accounts-table tbody",
      accounts
        .map(
          (a) => `<tr>
          <td>${a.name}</td>
          <td class="mono">${a.kind}</td>
          <td>${a.category}</td>
          <td>${money(a.balance)}</td>
          <td>${a.credit_limit ? money(a.credit_limit) : "—"}</td>
          <td>${a.utilization_pct != null ? pct(a.utilization_pct) : "—"}</td>
        </tr>`
        )
        .join("")
    );
  }

  function renderHoldings(holdings) {
    fillTable(
      "#holdings-table tbody",
      holdings
        .map(
          (h) => `<tr>
          <td>${h.account_name || h.account_id}</td>
          <td>${h.asset}</td>
          <td class="mono">${h.ticker || "—"}</td>
          <td>${h.quantity}</td>
          <td>${money(h.price)}</td>
          <td>${money(valueOf(h))}</td>
          <td class="mono">${h.asset_type}</td>
        </tr>`
        )
        .join("")
    );
  }

  function renderDebt(stack) {
    fillTable(
      "#debt-table tbody",
      stack
        .map(
          (d) => `<tr>
          <td>${d.name}</td>
          <td class="down">${money(d.balance)}</td>
          <td>${pct(d.pct_of_debt)}</td>
          <td>${d.utilization_pct != null ? pct(d.utilization_pct) : "—"}</td>
          <td>${d.apr_pct != null ? d.apr_pct.toFixed(1) + "%" : "—"}</td>
          <td>${d.payoff_months != null ? d.payoff_months.toFixed(1) : "—"}</td>
        </tr>`
        )
        .join("")
    );
  }

  function renderCashflow(cf) {
    fillTable(
      "#cashflow-table tbody",
      cf.waterfall
        .map(
          (b) => `<tr>
          <td>${b.name}</td>
          <td>${pct(b.fraction * 100)}</td>
          <td>${money(b.amount)}</td>
        </tr>`
        )
        .join("")
    );
    setText("kpi-paycheck", money(cf.paycheck));
    setText("kpi-scenario", cf.scenario);
  }

  function renderPhone(state) {
    const { buckets, accounts, stack, seed } = state;
    fillTable(
      "#phone-ytd tbody",
      `<tr><td>Assets</td><td>${money(buckets.assets)}</td></tr>
       <tr><td>Investments</td><td>${money(buckets.investments)}</td></tr>
       <tr><td>Liabilities</td><td class="down">${money(buckets.liabilities)}</td></tr>
       <tr><td><strong>Net worth</strong></td><td><strong>${money(buckets.net_worth)}</strong></td></tr>`
    );
    const cards = accounts.filter((a) => a.kind === "credit");
    fillTable(
      "#phone-cards tbody",
      cards
        .map((a) => {
          const rem = (a.credit_limit || 0) - a.balance;
          return `<tr>
            <td>${a.name}</td>
            <td>${a.apr_pct != null ? a.apr_pct.toFixed(2) + "%" : "—"}</td>
            <td>${money(rem)}</td>
            <td>${pct(a.utilization_pct)}</td>
          </tr>`;
        })
        .join("")
    );
    const home = buckets.home;
    fillTable(
      "#phone-sleeves tbody",
      Object.entries(home)
        .map(([k, v]) => `<tr><td class="mono">${k}</td><td>${money(v)}</td></tr>`)
        .join("")
    );
  }

  function charts(state) {
    if (typeof Chart === "undefined") return;
    const isDark = document.documentElement.getAttribute("data-theme") !== "light";
    const tick = isDark ? "#8b9cb3" : "#4a5a6e";
    const grid = isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.08)";

    const { stack, buckets, cp } = state;
    if (debtChart) debtChart.destroy();
    if (sleeveChart) sleeveChart.destroy();
    if (nwChart) nwChart.destroy();

    const debtCtx = document.getElementById("debt-chart");
    if (debtCtx) {
      debtChart = new Chart(debtCtx, {
        type: "doughnut",
        data: {
          labels: stack.map((d) => d.name),
          datasets: [{
            data: stack.map((d) => d.balance),
            backgroundColor: ["#f43f5e", "#f59e0b", "#a78bfa", "#3d9cf0", "#2dd4bf"],
            borderWidth: 0,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: "right", labels: { color: tick, boxWidth: 10 } } },
        },
      });
    }

    const sleeveCtx = document.getElementById("sleeve-chart");
    if (sleeveCtx) {
      const h = buckets.home;
      const labels = Object.keys(h).filter((k) => h[k] > 0);
      sleeveChart = new Chart(sleeveCtx, {
        type: "doughnut",
        data: {
          labels,
          datasets: [{
            data: labels.map((k) => h[k]),
            backgroundColor: ["#3d9cf0", "#2dd4bf", "#34d399", "#a78bfa", "#f59e0b", "#94a3b8", "#f43f5e", "#fb7185"],
            borderWidth: 0,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: "right", labels: { color: tick, boxWidth: 10 } } },
        },
      });
    }

    const nwCtx = document.getElementById("nw-chart");
    if (nwCtx) {
      nwChart = new Chart(nwCtx, {
        type: "line",
        data: {
          labels: cp.series.map((s) => s.as_of),
          datasets: [{
            label: "Net worth (synthetic)",
            data: cp.series.map((s) => s.net_worth),
            borderColor: "#3d9cf0",
            backgroundColor: "rgba(61,156,240,0.12)",
            fill: true,
            tension: 0.25,
            pointRadius: 2,
            borderWidth: 2,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { labels: { color: tick } } },
          scales: {
            x: { ticks: { color: tick, maxTicksLimit: 6 }, grid: { color: grid } },
            y: { ticks: { color: tick }, grid: { color: grid } },
          },
        },
      });
    }
  }

  function switchTab(name) {
    document.querySelectorAll("[data-tab-panel]").forEach((p) => {
      p.hidden = p.getAttribute("data-tab-panel") !== name;
    });
    document.querySelectorAll("[data-tab]").forEach((b) => {
      b.classList.toggle("active", b.getAttribute("data-tab") === name);
    });
  }

  function run() {
    const seed = window.WORKSHEET_SEED;
    if (!seed) {
      log("missing WORKSHEET_SEED", "warn");
      return;
    }
    const scenario =
      document.getElementById("scenario-select")?.value || "baseline";
    const asOf = seed.as_of;

    // Deep copy holdings so we never mutate seed
    const holdings = seed.holdings.map((h) => ({ ...h }));
    const accounts = rollupAccounts(seed, holdings);
    // Fix brokerage balance rollup already in accounts from holdings
    const buckets = computeBuckets(holdings);
    const stack = debtStack(accounts, holdings);
    const cp = cockpit(buckets, seed.snapshots, asOf);
    const rw = runway(seed, holdings);
    const cf = cashflow(seed, scenario);
    const card = cardOfDay(seed, asOf);

    // recompute account balances cleanly
    const accountsFinal = rollupAccounts(seed, holdings);

    const state = {
      seed,
      holdings,
      accounts: accountsFinal,
      buckets,
      stack,
      cp,
      rw,
      cf,
      card,
    };

    log("worksheet engine — synthetic persona " + seed.persona_name, "ok");
    log(
      `buckets NW=${buckets.net_worth.toFixed(2)} debt_facilities=${stack.length} scenario=${cf.scenario}`,
      "info"
    );

    document.getElementById("persona-label") &&
      (document.getElementById("persona-label").textContent = seed.persona_name);
    document.getElementById("disclaimer-banner") &&
      (document.getElementById("disclaimer-banner").textContent = seed.disclaimer);

    renderCockpit(state);
    renderAccounts(accountsFinal);
    renderHoldings(holdings);
    renderDebt(stack);
    renderCashflow(cf);
    renderPhone(state);
    charts(state);
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-tab]").forEach((btn) => {
      btn.addEventListener("click", () => switchTab(btn.getAttribute("data-tab")));
    });
    document.getElementById("run-demo")?.addEventListener("click", run);
    document.getElementById("scenario-select")?.addEventListener("change", run);
    switchTab("cockpit");
    run();
  });
})();
