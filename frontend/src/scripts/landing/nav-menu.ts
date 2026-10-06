import { syncHeaderHeight } from "./header-state";
import { attachPanelSwipe } from "./panel-swipe";

const TRIGGER = "[aria-controls][aria-expanded]";
const OPEN_CLASS = "is-open";
const HIDE_DELAY_MS = 170;
const MOBILE_PANEL_ID = "mobileMenuPanel";

function panelOf(trigger: Element): HTMLElement | null {
  const id = trigger.getAttribute("aria-controls");
  return id ? document.getElementById(id) : null;
}

function isOpen(trigger: Element): boolean {
  return trigger.getAttribute("aria-expanded") === "true";
}

function close(trigger: HTMLElement, restoreFocus = false): void {
  const panel = panelOf(trigger);
  if (!panel || !isOpen(trigger)) {
    return;
  }
  trigger.setAttribute("aria-expanded", "false");
  panel.classList.remove(OPEN_CLASS);
  window.setTimeout(() => {
    const live = panelOf(trigger);
    if (live && !isOpen(trigger)) {
      live.hidden = true;
    }
  }, HIDE_DELAY_MS);
  if (restoreFocus) {
    trigger.focus();
  }
}

function closeAll(except: HTMLElement | null): void {
  document.querySelectorAll<HTMLElement>(TRIGGER).forEach((trigger) => {
    if (trigger === except || (except && panelOf(trigger)?.contains(except))) {
      return;
    }
    close(trigger);
  });
}

function open(trigger: HTMLElement): void {
  const panel = panelOf(trigger);
  if (!panel) {
    return;
  }
  closeAll(trigger);
  syncHeaderHeight();
  panel.hidden = false;
  void panel.offsetWidth;
  panel.style.transform = "";
  panel.style.opacity = "";
  panel.style.transition = "";
  if (panel.id === MOBILE_PANEL_ID) {
    attachPanelSwipe(panel, () => {
      close(trigger, true);
    });
  }
  panel.classList.add(OPEN_CLASS);
  trigger.setAttribute("aria-expanded", "true");
}

function onClick(event: MouseEvent): void {
  const target = event.target instanceof Element ? event.target : null;
  const trigger = target?.closest<HTMLElement>(TRIGGER);
  if (trigger && panelOf(trigger)) {
    event.preventDefault();
    if (isOpen(trigger)) {
      close(trigger);
    } else {
      open(trigger);
    }
    return;
  }
  if (!target?.closest(".dpo-menu-panel")) {
    closeAll(null);
  }
}

export function setupNavMenu(): void {
  document.addEventListener("click", onClick);
  document.addEventListener("keydown", (event) => {
    const opened = document.querySelector<HTMLElement>(`${TRIGGER}[aria-expanded="true"]`);
    if (event.key === "Escape" && opened) {
      close(opened, true);
    }
  });
  document.addEventListener("focusin", (event) => {
    const target = event.target instanceof Element ? event.target : null;
    if (!target?.closest("header") && !target?.closest(".dpo-menu-panel")) {
      closeAll(null);
    }
  });
}
