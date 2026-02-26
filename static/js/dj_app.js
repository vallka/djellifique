(function () {
  const root = document.documentElement;

  // ---- Theme toggle (unchanged) ----
  const THEME_KEY = "admin_theme";
  const saved = localStorage.getItem(THEME_KEY);
  if (saved === "light" || saved === "dark") root.dataset.theme = saved;

  document.addEventListener("click", (e) => {
    const t = e.target.closest("[data-theme-toggle]");
    if (!t) return;
    const next = root.dataset.theme === "light" ? "dark" : "light";
    root.dataset.theme = next;
    localStorage.setItem(THEME_KEY, next);
  });

  // ---- Sidebar toggle (simple + persistent on desktop) ----
  const SIDEBAR_KEY = "admin_sidebar_hidden"; // "1" means hidden on desktop
  const app = document.querySelector(".app");
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.querySelector("[data-backdrop]");

  function isMobile() {
    return window.matchMedia("(max-width: 980px)").matches;
  }

  function setDesktopSidebarHidden(hidden) {
    if (hidden) localStorage.setItem(SIDEBAR_KEY, "1");
    else localStorage.removeItem(SIDEBAR_KEY);
  }

  function restoreDesktopSidebarState() {
    if (!app) return;
    if (isMobile()) {
      // Mobile: never use persisted desktop state
      app.classList.remove("sidebar-hidden");
      return;
    }
    const hidden = localStorage.getItem(SIDEBAR_KEY) === "1";
    app.classList.toggle("sidebar-hidden", hidden);
  }

  // Restore state on load
  restoreDesktopSidebarState();

  function openSidebar() {
    if (!app || !sidebar) return;

    if (isMobile()) {
      sidebar.classList.add("is-open");
      if (backdrop) backdrop.hidden = false;
      document.body.style.overflow = "hidden";
    } else {
      app.classList.remove("sidebar-hidden");
      setDesktopSidebarHidden(false);
    }
  }

  function closeSidebar() {
    if (!app || !sidebar) return;

    if (isMobile()) {
      sidebar.classList.remove("is-open");
      if (backdrop) backdrop.hidden = true;
      document.body.style.overflow = "";
    } else {
      app.classList.add("sidebar-hidden");
      setDesktopSidebarHidden(true);
    }
  }

  document.addEventListener("click", (e) => {
    if (e.target.closest("[data-sidebar-open]")) openSidebar();
    if (e.target.closest("[data-sidebar-close]")) closeSidebar();
    if (e.target.closest("[data-backdrop]")) closeSidebar();

    // ---- Clickable table rows ----
    const row = e.target.closest("tr[data-id_order]");
    if (!row) return;

    // Don't trigger if clicking an actual link, button, input etc.
    if (e.target.closest("a, button, input, select, textarea")) return;

    const link = row.querySelector("a[href]");
    if (link) link.click();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeSidebar();
  });

  // If user resizes between mobile/desktop, apply desktop persisted state
  window.addEventListener("resize", () => {
    restoreDesktopSidebarState();
  });
})();