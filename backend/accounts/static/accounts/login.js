"use strict";

(() => {
  const DIGIT = /\d/g;
  const SUCCESS_PAUSE_MS = 900;
  const ERROR_PAUSE_MS = 650;
  const MIN_CHECK_MS = 600;
  const LOCKED = 429;
  const SHOW_SECRET = "Показать пароль";
  const HIDE_SECRET = "Скрыть пароль";
  const SCRIPT_HEADERS = { "X-Requested-With": "XMLHttpRequest", Accept: "application/json" };

  function toggleSecret(toggle, input) {
    const shown = toggle.getAttribute("aria-pressed") !== "true";
    input.type = shown ? "text" : "password";
    toggle.setAttribute("aria-pressed", String(shown));
    toggle.setAttribute("aria-label", shown ? HIDE_SECRET : SHOW_SECRET);
    input.focus();
  }

  function setupSecret(toggle) {
    const input = toggle.closest(".glass-secret").querySelector("[data-secret]");
    toggle.hidden = false;
    toggle.addEventListener("click", () => toggleSecret(toggle, input));
  }

  function digitsOf(text, limit) {
    return (text.match(DIGIT) || []).join("").slice(0, limit);
  }

  function makeCell(index) {
    const cell = document.createElement("span");
    cell.className = "glass-cell";
    cell.setAttribute("aria-hidden", "true");
    cell.style.setProperty("--i", String(index));
    return cell;
  }

  function buildCells(box, count) {
    box.style.setProperty("--digits", String(count));
    box.style.setProperty("--middle", String((count - 1) / 2));
    const cells = Array.from({ length: count }, (_, index) => makeCell(index));
    box.prepend(...cells);
    box.classList.add("is-enhanced");
    return cells;
  }

  function paint(view) {
    const value = view.input.value;
    const active = Math.min(value.length, view.count - 1);
    view.cells.forEach((cell, index) => {
      cell.textContent = value[index] || "";
      cell.classList.toggle("is-active", index === active);
    });
  }

  function showError(view, message) {
    view.error.textContent = message;
    view.error.hidden = false;
  }

  function hideError(view) {
    view.error.hidden = true;
  }

  function succeed(view, address) {
    view.box.classList.replace("is-checking", "is-success");
    view.card.classList.add("is-success");
    view.title.textContent = view.form.dataset.successTitle;
    view.lead.textContent = view.form.dataset.successLead;
    window.setTimeout(() => window.location.assign(address), SUCCESS_PAUSE_MS);
  }

  function reset(view) {
    view.box.classList.remove("is-error");
    view.input.value = "";
    view.input.readOnly = false;
    view.busy = false;
    paint(view);
    view.input.focus();
  }

  function fail(view, message) {
    view.box.classList.remove("is-checking");
    view.box.classList.add("is-error");
    showError(view, message);
    window.setTimeout(() => reset(view), ERROR_PAUSE_MS);
  }

  function lock(view) {
    view.box.classList.remove("is-checking");
    view.box.classList.add("is-locked");
    view.input.disabled = true;
    showError(view, view.form.dataset.lockedMessage);
  }

  function pause(ms) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
  }

  function isJson(response) {
    return (response.headers.get("Content-Type") || "").includes("application/json");
  }

  async function answer(view, response) {
    if (!isJson(response)) {
      window.location.assign(response.url);
      return;
    }
    if (response.status === LOCKED) {
      lock(view);
      return;
    }
    const data = await response.json();
    if (response.ok) {
      succeed(view, data.redirect);
      return;
    }
    fail(view, data.error);
  }

  async function verify(view) {
    if (view.busy) {
      return;
    }
    view.busy = true;
    view.input.readOnly = true;
    hideError(view);
    view.box.classList.add("is-checking");
    const request = { method: "POST", body: new FormData(view.form), headers: SCRIPT_HEADERS, credentials: "same-origin" };
    try {
      const [response] = await Promise.all([fetch(view.form.action, request), pause(MIN_CHECK_MS)]);
      await answer(view, response);
    } catch {
      view.form.submit();
    }
  }

  function typed(view) {
    view.input.value = digitsOf(view.input.value, view.count);
    paint(view);
    if (view.input.value.length === view.count) {
      verify(view);
    }
  }

  function keepCaretAtEnd(input) {
    const end = input.value.length;
    input.setSelectionRange(end, end);
  }

  function watchFocus(view) {
    view.input.addEventListener("focus", () => view.box.classList.add("has-focus"));
    view.input.addEventListener("blur", () => view.box.classList.remove("has-focus"));
    view.input.addEventListener("click", () => keepCaretAtEnd(view.input));
    view.input.addEventListener("keyup", () => keepCaretAtEnd(view.input));
  }

  function codeView(form) {
    const card = form.closest(".glass-card");
    const box = form.querySelector("[data-code-cells]");
    const count = Number(form.dataset.digits);
    return {
      form,
      card,
      box,
      count,
      input: form.querySelector("[data-code-input]"),
      error: form.querySelector("[data-code-error]"),
      title: card.querySelector("#glass-title"),
      lead: card.querySelector("#glass-lead"),
      cells: buildCells(box, count),
      busy: false,
    };
  }

  function setupCode(form) {
    const view = codeView(form);
    form.classList.add("is-enhanced");
    view.input.maxLength = view.count;
    view.input.addEventListener("input", () => typed(view));
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      verify(view);
    });
    watchFocus(view);
    paint(view);
    if (document.activeElement === view.input) {
      view.box.classList.add("has-focus");
    }
  }

  document.querySelectorAll("[data-secret-toggle]").forEach(setupSecret);
  document.querySelectorAll("[data-code]").forEach(setupCode);
})();
