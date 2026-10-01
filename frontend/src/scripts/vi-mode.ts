const STORAGE_KEY = "vi-mode";
const ENABLED = "1";
const DISABLED = "0";
const CLASS_NAME = "vi-mode";

function remember(enabled: boolean): void {
  try {
    localStorage.setItem(STORAGE_KEY, enabled ? ENABLED : DISABLED);
  } catch {
    return;
  }
}

function remembered(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === ENABLED;
  } catch {
    return false;
  }
}

function apply(button: HTMLElement, enabled: boolean): void {
  document.documentElement.classList.toggle(CLASS_NAME, enabled);
  button.setAttribute("aria-pressed", String(enabled));
}

export function setupViMode(button: HTMLElement): void {
  button.addEventListener("click", () => {
    const enabled = !document.documentElement.classList.contains(CLASS_NAME);
    apply(button, enabled);
    remember(enabled);
  });
  if (remembered()) {
    apply(button, true);
  }
}
