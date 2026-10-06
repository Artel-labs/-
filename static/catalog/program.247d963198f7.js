"use strict";

(() => {
  const POLL_MS = 5000;
  const ERRORS = ".errorlist, .errors, [data-testid=error-count]";

  const showTab = (key) => window.dispatchEvent(new CustomEvent("dpo-tab", { detail: key }));

  const openFirstError = () => {
    const error = document.querySelector(ERRORS);
    const panel = error?.closest("[data-dpo-tab]");
    if (panel) showTab(panel.dataset.dpoTab);
    error?.closest("details.dpo-inline")?.setAttribute("open", "");
  };

  const watchSync = () => {
    const url = document.querySelector("[data-sync-running]")?.dataset.syncRunning;
    if (!url) return;
    const check = async () => {
      try {
        const response = await fetch(url, { headers: { Accept: "application/json" }, credentials: "same-origin" });
        const state = await response.json();
        if (!state.running) {
          window.location.reload();
          return;
        }
      } catch {
        return;
      }
      window.setTimeout(check, POLL_MS);
    };
    window.setTimeout(check, POLL_MS);
  };

  document.addEventListener("alpine:initialized", openFirstError);

  const start = () => watchSync();

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
