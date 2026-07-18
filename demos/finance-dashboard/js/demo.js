/**
 * Browser live demo — mirrors Python analytics conceptually.
 * Uses deterministic mock series (same idea as MockMarketClient) so
 * GitHub Pages works without API keys or CORS pain.
 *
 * Extension: replace fetchQuotes() with a serverless proxy to Alpha Vantage.
 */
(function () {
  "use strict";

  const SEED = {
    AAPL: 190,
    MSFT: 420,
    GOOGL: 175,
    "BTC-USD": 65000,
    VTI: 260,
    AMZN: 185,
    SPY: 520,
  };

  const DEFAULT_HOLDINGS = [
    { symbol: "AAPL", shares: 25, cost_basis: 165 },
    { symbol: "MSFT", shares: 15, cost_basis: 320 },
    { symbol: "GOOGL", shares: 20, cost_basis: 130 },
    { symbol: "BTC-USD", shares: 0.15, cost_basis: 42000 },
    { symbol: "VTI", shares: 40, cost_basis: 220 },
  ];

  let priceChart = null;
  let allocChart = null;

  function hashInt(s) {
    let h = 0;
    for (let i = 0; i < s.length; i++) h = (Math.imul(31, h) + s.charCodeAt(i)) | 0;
    return Math.abs(h);
  }

  function priceFor(symbol, dayIndex) {
    const base = SEED[symbol] ?? 100 + (hashInt(symbol) % 50);
    const drift = 1 + 0.0002 * ((dayIndex % 365) - 180);
    const wave = 1 + 0.02 * Math.sin(dayIndex / 12 + (hashInt(symbol) % 7));
    const noise = 1 + 0.005 * Math.sin(dayIndex * 0.7 + hashInt(symbol));
    return base * drift * wave * noise;
  }

  function log(msg, cls) {
    const el = document.getElementById("demo-log");
    if (!el) return;
    const line = document.createElement("div");
    line.className = cls || "info";
    const ts = new Date().toISOString().slice(11, 19);
    line.textContent = `${ts} | ${msg}`;
    el.prepend(line);
  }

  function parseHoldings(text) {
    // format: AAPL:25@165, MSFT:15@320
    if (!text || !text.trim()) return DEFAULT_HOLDINGS.slice();
    return text.split(",").map((part) => {
      const m = part.trim().match(/^([A-Za-z0-9.-]+):([\d.]+)@([\d.]+)$/);
      if (!m) throw new Error(`Bad holding '${part}'. Use SYM:shares@cost`);
      return {
        symbol: m[1].toUpperCase(),
        shares: parseFloat(m[2]),
        cost_basis: parseFloat(m[3]),
      };
    });
  }

  function buildHistory(symbol, days) {
    const today = new Date();
    const bars = [];
    for (let i = days; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      if (d.getDay() === 0 || d.getDay() === 6) {
        if (!symbol.endsWith("-USD")) continue;
      }
      const dayIndex = Math.floor(d.getTime() / 86400000);
      const close = priceFor(symbol, dayIndex);
      bars.push({
        date: d.toISOString().slice(0, 10),
        close: +close.toFixed(4),
      });
    }
    return bars;
  }

  function runPipeline(holdings, cash, historyDays, expectedReturn, years) {
    log(`ETL extract — provider=mock symbols=${holdings.map((h) => h.symbol).join(",")}`, "info");
    const positions = holdings.map((h) => {
      const dayIndex = Math.floor(Date.now() / 86400000);
      const price = priceFor(h.symbol, dayIndex);
      const prev = priceFor(h.symbol, dayIndex - 1);
      const market_value = price * h.shares;
      const cost_total = h.cost_basis * h.shares;
      const unrealized_pnl = market_value - cost_total;
      return {
        ...h,
        price,
        market_value,
        cost_total,
        unrealized_pnl,
        unrealized_pnl_pct: cost_total ? (unrealized_pnl / cost_total) * 100 : 0,
        day_change_pct: prev ? ((price - prev) / prev) * 100 : 0,
      };
    });

    const equity = positions.reduce((s, p) => s + p.market_value, 0);
    const total = equity + cash;
    positions.forEach((p) => {
      p.weight_pct = total ? (p.market_value / total) * 100 : 0;
    });

    const primary = holdings[0]?.symbol || "AAPL";
    const history = buildHistory(primary, historyDays);
    log(`ETL transform — positions=${positions.length} history_bars=${history.length}`, "ok");

    // projection
    let value = total;
    const projection = [{ year: 0, value }];
    for (let y = 1; y <= years; y++) {
      value = value * (1 + expectedReturn);
      projection.push({ year: y, value });
    }

    const returns = [];
    for (let i = 1; i < history.length; i++) {
      returns.push((history[i].close - history[i - 1].close) / history[i - 1].close);
    }
    const mean =
      returns.reduce((a, b) => a + b, 0) / (returns.length || 1);
    const variance =
      returns.reduce((a, b) => a + (b - mean) ** 2, 0) / (returns.length || 1);
    const annVol = Math.sqrt(variance * 252);

    log(`analytics — total MV $${total.toFixed(2)} ann_vol≈${(annVol * 100).toFixed(1)}%`, "ok");

    return {
      positions,
      cash,
      total,
      equity,
      pnl: positions.reduce((s, p) => s + p.unrealized_pnl, 0),
      primary,
      history,
      projection,
      annVol,
      expectedReturn,
    };
  }

  function fmt(n, d = 2) {
    return n.toLocaleString(undefined, {
      minimumFractionDigits: d,
      maximumFractionDigits: d,
    });
  }

  function renderKPIs(data) {
    const set = (id, text, cls) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.textContent = text;
      el.className = "kpi-value" + (cls ? " " + cls : "");
    };
    set("kpi-total", `$${fmt(data.total)}`);
    set(
      "kpi-pnl",
      `${data.pnl >= 0 ? "+" : ""}$${fmt(data.pnl)}`,
      data.pnl >= 0 ? "up" : "down"
    );
    set("kpi-cash", `$${fmt(data.cash)}`);
    set("kpi-vol", `${(data.annVol * 100).toFixed(1)}%`);
    set("kpi-symbols", String(data.positions.length));
    set("kpi-provider", "mock");
  }

  function renderTable(positions) {
    const tbody = document.querySelector("#positions-table tbody");
    if (!tbody) return;
    tbody.innerHTML = positions
      .map((p) => {
        const cls = p.unrealized_pnl >= 0 ? "up" : "down";
        return `<tr>
          <td class="mono">${p.symbol}</td>
          <td>${p.shares}</td>
          <td>$${fmt(p.price)}</td>
          <td>$${fmt(p.market_value)}</td>
          <td class="${cls}">${p.unrealized_pnl >= 0 ? "+" : ""}$${fmt(p.unrealized_pnl)}</td>
          <td>${p.weight_pct.toFixed(1)}%</td>
          <td class="${p.day_change_pct >= 0 ? "up" : "down"}">${p.day_change_pct.toFixed(2)}%</td>
        </tr>`;
      })
      .join("");
  }

  function renderCharts(data) {
    const priceCtx = document.getElementById("price-chart");
    const allocCtx = document.getElementById("alloc-chart");
    if (!priceCtx || !allocCtx || typeof Chart === "undefined") return;

    if (priceChart) priceChart.destroy();
    if (allocChart) allocChart.destroy();

    const isDark =
      document.documentElement.getAttribute("data-theme") !== "light";
    const grid = isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.08)";
    const tick = isDark ? "#8b9cb3" : "#4a5a6e";

    priceChart = new Chart(priceCtx, {
      type: "line",
      data: {
        labels: data.history.map((b) => b.date),
        datasets: [
          {
            label: `${data.primary} close (mock)`,
            data: data.history.map((b) => b.close),
            borderColor: "#3d9cf0",
            backgroundColor: "rgba(61,156,240,0.12)",
            fill: true,
            tension: 0.25,
            pointRadius: 0,
            borderWidth: 2,
          },
        ],
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

    const labels = data.positions.map((p) => p.symbol).concat(["CASH"]);
    const values = data.positions
      .map((p) => p.market_value)
      .concat([data.cash]);
    const colors = [
      "#3d9cf0",
      "#2dd4bf",
      "#f59e0b",
      "#a78bfa",
      "#34d399",
      "#f43f5e",
      "#94a3b8",
    ];

    allocChart = new Chart(allocCtx, {
      type: "doughnut",
      data: {
        labels,
        datasets: [
          {
            data: values,
            backgroundColor: colors.slice(0, labels.length),
            borderWidth: 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "right",
            labels: { color: tick, boxWidth: 12 },
          },
        },
      },
    });

    // projection spark in KPI area table
    const projEl = document.getElementById("projection-note");
    if (projEl) {
      const last = data.projection[data.projection.length - 1];
      projEl.textContent = `Simple projection: $${fmt(last.value)} in ${last.year}y @ ${(data.expectedReturn * 100).toFixed(1)}% assumed annual (educational).`;
    }
  }

  function refresh() {
    try {
      const holdingsText = document.getElementById("holdings-input")?.value;
      const cash = parseFloat(document.getElementById("cash-input")?.value || "5000");
      const days = parseInt(document.getElementById("days-input")?.value || "90", 10);
      const ret = parseFloat(document.getElementById("return-input")?.value || "7") / 100;
      const years = parseInt(document.getElementById("years-input")?.value || "10", 10);
      const holdings = parseHoldings(holdingsText);
      const data = runPipeline(holdings, cash, days, ret, years);
      renderKPIs(data);
      renderTable(data.positions);
      renderCharts(data);
    } catch (err) {
      log(String(err.message || err), "warn");
      console.error(err);
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    const holdingsInput = document.getElementById("holdings-input");
    if (holdingsInput && !holdingsInput.value) {
      holdingsInput.value = DEFAULT_HOLDINGS.map(
        (h) => `${h.symbol}:${h.shares}@${h.cost_basis}`
      ).join(", ");
    }
    document.getElementById("run-demo")?.addEventListener("click", refresh);
    document.getElementById("reset-demo")?.addEventListener("click", () => {
      if (holdingsInput) {
        holdingsInput.value = DEFAULT_HOLDINGS.map(
          (h) => `${h.symbol}:${h.shares}@${h.cost_basis}`
        ).join(", ");
      }
      const cash = document.getElementById("cash-input");
      if (cash) cash.value = "5000";
      refresh();
    });
    refresh();
    log("pipeline ready — mock provider (Pages-safe)", "ok");
  });
})();
