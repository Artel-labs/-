"use strict";

(() => {
  const SELECTING = "dpo-selecting";
  const CLICKABLE = "dpo-row-link";
  const INTERACTIVE = "a, button, input, select, textarea, label, summary, [contenteditable]";
  const FIELDS = "input, select, textarea, button";
  const LABELS = { off: "Выбрать", on: "Готово" };

  const changelist = () => document.getElementById("changelist");
  const toggleAll = () => document.getElementById("action-toggle");
  const boxes = () => Array.from(document.querySelectorAll("#result_list input.action-select"));
  const rows = () => Array.from(document.querySelectorAll("#result_list tr.data-row"));
  const rowLink = (row) => row.querySelector("th a[href], td a[href]");
  const isSelecting = () => Boolean(changelist()?.classList.contains(SELECTING));
  const hasSelection = () => boxes().some((box) => box.checked);

  const showCount = () => {
    const count = boxes().filter((box) => box.checked).length;
    document.querySelectorAll("[data-selected-count]").forEach((el) => {
      el.textContent = String(count);
    });
  };

  const selectAll = () => {
    const all = toggleAll();
    if (all && !all.checked) all.click();
    showCount();
  };

  const clearSelection = () => {
    const all = toggleAll();
    if (!all || !hasSelection()) return;
    if (!all.checked) all.click();
    all.click();
    showCount();
  };

  const setSelecting = (on) => {
    changelist()?.classList.toggle(SELECTING, on);
    document.querySelectorAll("[data-select-toggle]").forEach((button) => {
      button.setAttribute("aria-pressed", String(on));
      const label = button.querySelector("[data-select-label]");
      if (label) label.textContent = on ? LABELS.on : LABELS.off;
    });
    if (!on) clearSelection();
  };

  const openRow = (row, event) => {
    const link = rowLink(row);
    if (!link) return;
    if (event.ctrlKey || event.metaKey) {
      window.open(link.href, "_blank", "noopener");
      return;
    }
    window.location.assign(link.href);
  };

  const pickRow = (row, event) => {
    if (event.target.closest(FIELDS)) return;
    event.preventDefault();
    row.querySelector("input.action-select")?.click();
  };

  const onRowClick = (event) => {
    const row = event.target.closest("#result_list tr.data-row");
    if (!row) return;
    if (isSelecting()) return pickRow(row, event);
    if (event.target.closest(INTERACTIVE)) return;
    if (String(window.getSelection?.() ?? "").length > 0) return;
    openRow(row, event);
  };

  const onClick = (event) => {
    const target = event.target;
    if (target.closest("[data-select-toggle]")) return setSelecting(!isSelecting());
    if (target.closest("[data-select-all]")) return selectAll();
    if (target.closest("[data-select-none]")) return clearSelection();
    const action = target.closest("[data-action]");
    if (action) {
      const input = action.form?.querySelector('input[name="action"]');
      if (input) input.value = action.dataset.action;
      return;
    }
    onRowClick(event);
  };

  const onChange = (event) => {
    if (event.target.matches("input.action-select, #action-toggle")) showCount();
  };

  const markRows = () => {
    rows().forEach((row) => row.classList.toggle(CLICKABLE, Boolean(rowLink(row))));
  };

  const start = () => {
    markRows();
    if (hasSelection()) setSelecting(true);
    showCount();
    document.addEventListener("click", onClick);
    document.addEventListener("change", onChange);
    window.addEventListener("pageshow", () => {
      if (hasSelection()) setSelecting(true);
      showCount();
    });
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
