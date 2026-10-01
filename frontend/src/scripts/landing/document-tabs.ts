const ORDER = ["pk", "pp", "vo", "cert"];
const KEYS: Record<string, (index: number) => number> = {
  ArrowRight: (index) => (index + 1) % ORDER.length,
  ArrowDown: (index) => (index + 1) % ORDER.length,
  ArrowLeft: (index) => (index - 1 + ORDER.length) % ORDER.length,
  ArrowUp: (index) => (index - 1 + ORDER.length) % ORDER.length,
  Home: () => 0,
  End: () => ORDER.length - 1,
};

let current = ORDER[0] ?? "";

function activate(key: string, focusTab = false): void {
  if (!ORDER.includes(key)) {
    return;
  }
  document.querySelectorAll<HTMLElement>("[data-dpo-doc]").forEach((tab) => {
    const on = tab.dataset.dpoDoc === key;
    tab.classList.toggle("is-active", on);
    tab.setAttribute("aria-selected", String(on));
    if (on) {
      tab.removeAttribute("tabindex");
      if (focusTab) {
        tab.focus();
      }
    } else {
      tab.setAttribute("tabindex", "-1");
    }
  });
  document.querySelectorAll<HTMLElement>("[data-dpo-doc-item]").forEach((item) => {
    const show = item.dataset.dpoDocItem === key;
    item.classList.toggle("is-doc-current", show);
    item.hidden = !show;
  });
  const view = document.getElementById("docView");
  const tab = document.getElementById(`docTab-${key}`);
  if (view && tab) {
    view.setAttribute("aria-labelledby", tab.id);
  }
  current = key;
}

function nextKey(): string {
  return ORDER[(ORDER.indexOf(current) + 1) % ORDER.length] ?? current;
}

export function setupDocumentTabs(): void {
  document.addEventListener("click", (event) => {
    const target = event.target instanceof Element ? event.target : null;
    const tab = target?.closest<HTMLElement>("[data-dpo-doc]");
    if (tab) {
      activate(tab.dataset.dpoDoc ?? "");
    } else if (target?.closest(".dpo-doc-view")) {
      activate(nextKey());
    }
  });
  document.addEventListener("keydown", (event) => {
    const tab = event.target instanceof Element ? event.target.closest<HTMLElement>("[data-dpo-doc]") : null;
    const move = KEYS[event.key];
    if (!tab || !move) {
      return;
    }
    event.preventDefault();
    activate(ORDER[move(ORDER.indexOf(tab.dataset.dpoDoc ?? ""))] ?? current, true);
  });
}
