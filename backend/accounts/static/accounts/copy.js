"use strict";

(() => {
  const RESET_MS = 2000;

  function flash(button) {
    const label = button.textContent;
    button.textContent = button.dataset.copied;
    window.setTimeout(() => {
      button.textContent = label;
    }, RESET_MS);
  }

  function select(source) {
    const range = document.createRange();
    range.selectNodeContents(source);
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(range);
  }

  async function copy(button) {
    const source = document.getElementById(button.dataset.copy);
    try {
      await navigator.clipboard.writeText(source.textContent.trim());
      flash(button);
    } catch {
      select(source);
    }
  }

  document.querySelectorAll("[data-copy]").forEach((button) => {
    button.addEventListener("click", () => copy(button));
  });
})();
