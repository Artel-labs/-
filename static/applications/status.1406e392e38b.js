"use strict";

(() => {
  const TOAST_MS = 2500;
  const FAILED = "Статус не сохранён. Обновите страницу и попробуйте ещё раз.";
  const STATUS_PREFIX = "dpo-status-";
  const BASE_CLASS = "dpo-status-select";

  const csrfToken = () => document.querySelector("[name=csrfmiddlewaretoken]")?.value ?? "";

  const toast = (text, failed = false) => {
    const note = document.createElement("div");
    note.className = failed ? "dpo-toast is-error" : "dpo-toast";
    note.setAttribute("role", "status");
    note.textContent = text;
    document.body.append(note);
    window.setTimeout(() => note.remove(), TOAST_MS);
  };

  const saveStatus = async (url, status) => {
    const response = await fetch(url, {
      method: "POST",
      headers: { Accept: "application/json", "X-CSRFToken": csrfToken() },
      body: new URLSearchParams({ status }),
      credentials: "same-origin",
    });
    if (!response.ok) throw new Error(String(response.status));
    return response.json();
  };

  const paint = (select, status) => {
    Array.from(select.classList)
      .filter((name) => name.startsWith(STATUS_PREFIX) && name !== BASE_CLASS)
      .forEach((name) => select.classList.remove(name));
    select.classList.add(`${STATUS_PREFIX}${status}`);
    select.dataset.current = status;
  };

  const onSelect = async (select) => {
    const previous = select.dataset.current;
    select.disabled = true;
    try {
      const saved = await saveStatus(select.dataset.statusUrl, select.value);
      paint(select, saved.status);
      toast(`Статус: ${saved.label}`);
    } catch {
      select.value = previous;
      toast(FAILED, true);
    } finally {
      select.disabled = false;
    }
  };

  const press = (form, status) => {
    form.querySelectorAll("button[name=status]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.value === status));
    });
  };

  const onSwitch = async (form, button) => {
    try {
      const saved = await saveStatus(form.action, button.value);
      press(form, saved.status);
      toast(`Статус: ${saved.label}`);
    } catch {
      toast(FAILED, true);
    }
  };

  document.addEventListener(
    "change",
    (event) => {
      const select = event.target.closest("select[data-status-url]");
      if (!select) return;
      event.stopPropagation();
      onSelect(select);
    },
    true,
  );

  document.addEventListener("submit", (event) => {
    const form = event.target.closest("form[data-status-form]");
    const button = event.submitter;
    if (!form || !button || button.name !== "status") return;
    event.preventDefault();
    onSwitch(form, button);
  });
})();
