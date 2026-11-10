/**
 * app.js
 * ------
 * App shell behavior: tab/view switching, mobile sidebar toggle, and
 * dark-mode theme persistence. This is the last script loaded and wires
 * together the static shell around the feature modules.
 */

(() => {
  const VIEW_TITLES = {
    dashboard: "Dashboard",
    upload: "Upload Documents",
    chat: "Chat",
    documents: "Document Library",
    usage: "Usage & Cost",
  };

  function switchView(viewName) {
    document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
    const target = document.getElementById(`view-${viewName}`);
    if (target) target.classList.add("active");

    document.querySelectorAll(".nav-item").forEach((item) => {
      item.classList.toggle("active", item.dataset.view === viewName);
    });

    const titleEl = document.getElementById("viewTitle");
    if (titleEl) titleEl.textContent = VIEW_TITLES[viewName] || "Dashboard";

    // Close mobile sidebar after navigating.
    document.getElementById("sidebar")?.classList.remove("open");
  }

  function initNav() {
    document.querySelectorAll(".nav-item").forEach((item) => {
      item.addEventListener("click", () => {
        const view = item.dataset.view;
        if (view && document.getElementById(`view-${view}`)) {
          switchView(view);
        }
      });
    });
  }

  function initMobileMenu() {
    const toggle = document.getElementById("menuToggle");
    const sidebar = document.getElementById("sidebar");
    if (toggle && sidebar) {
      toggle.addEventListener("click", () => sidebar.classList.toggle("open"));
    }
  }

  function initTheme() {
    const toggle = document.getElementById("themeToggle");
    const stored = localStorage.getItem("enterprise_rag_theme");
    const initial = stored || "light";
    document.documentElement.setAttribute("data-theme", initial);

    if (toggle) {
      toggle.addEventListener("click", () => {
        const current = document.documentElement.getAttribute("data-theme");
        const next = current === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", next);
        localStorage.setItem("enterprise_rag_theme", next);
      });
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    initNav();
    initMobileMenu();
    initTheme();
  });
})();
