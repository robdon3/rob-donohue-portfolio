/**
 * Portfolio site interactions: nav, theme, smooth active states.
 */
(function () {
  "use strict";

  const THEME_KEY = "rd-portfolio-theme";

  function initTheme() {
    const stored = localStorage.getItem(THEME_KEY);
    const prefersLight =
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: light)").matches;
    const theme = stored || (prefersLight ? "light" : "dark");
    document.documentElement.setAttribute("data-theme", theme);
    updateThemeToggle(theme);
  }

  function updateThemeToggle(theme) {
    const btn = document.getElementById("theme-toggle");
    if (!btn) return;
    btn.setAttribute("aria-label", theme === "dark" ? "Switch to light mode" : "Switch to dark mode");
    btn.title = theme === "dark" ? "Light mode" : "Dark mode";
    btn.textContent = theme === "dark" ? "☀" : "☾";
  }

  function toggleTheme() {
    const current =
      document.documentElement.getAttribute("data-theme") || "dark";
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem(THEME_KEY, next);
    updateThemeToggle(next);
  }

  function initNav() {
    const toggle = document.getElementById("nav-toggle");
    const links = document.getElementById("nav-links");
    if (toggle && links) {
      toggle.addEventListener("click", () => {
        links.classList.toggle("open");
        const open = links.classList.contains("open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
      });
      links.querySelectorAll("a").forEach((a) => {
        a.addEventListener("click", () => links.classList.remove("open"));
      });
    }

    // Active section highlighting
    const sections = document.querySelectorAll("section[id]");
    const navAnchors = document.querySelectorAll('.nav-links a[href^="#"]');
    if (!sections.length || !navAnchors.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const id = entry.target.getAttribute("id");
          navAnchors.forEach((a) => {
            a.classList.toggle(
              "active",
              a.getAttribute("href") === `#${id}`
            );
          });
        });
      },
      { rootMargin: "-40% 0px -50% 0px", threshold: 0 }
    );
    sections.forEach((s) => observer.observe(s));
  }

  function initYear() {
    const el = document.getElementById("year");
    if (el) el.textContent = String(new Date().getFullYear());
  }

  document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initNav();
    initYear();
    const themeBtn = document.getElementById("theme-toggle");
    if (themeBtn) themeBtn.addEventListener("click", toggleTheme);
  });
})();
