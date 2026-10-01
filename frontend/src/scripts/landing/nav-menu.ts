import { syncHeaderHeight } from "./header-state";
import { attachPanelSwipe } from "./panel-swipe";

const TRIGGER = "[aria-controls][aria-expanded]";
const OPEN_CLASS = "is-open";
const HIDE_DELAY_MS = 170;
const HOVER_CLOSE_MS = 220;
const MOBILE_PANEL_ID = "mobileMenuPanel";

let hoverTimer = 0;
let clickClosed: HTMLElement | null = null;

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

function fillMobileDirs(panel: HTMLElement): void {
  const list = panel.querySelector(".dpo-mobile-dirs");
  const rows = document.querySelectorAll("#navProgramsPanel .dpo-menu-sphere-head, #navProgramsPanel .dpo-menu-all");
  if (list && rows.length) {
    list.replaceChildren(...[...rows].map((row) => row.cloneNode(true)));
  }
}

function open(trigger: HTMLElement): void {
  const panel = panelOf(trigger);
  if (!panel) {
    return;
  }
  closeAll(trigger);
  syncHeaderHeight();
  if (panel.id === MOBILE_PANEL_ID) {
    fillMobileDirs(panel);
  }
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

function canHover(): boolean {
  return window.matchMedia("(hover: hover) and (pointer: fine)").matches;
}

function cancelHoverClose(): void {
  window.clearTimeout(hoverTimer);
  hoverTimer = 0;
}

function triggerOfPanel(panel: Element | null): HTMLElement | null {
  if (!panel?.id) {
    return null;
  }
  return document.querySelector<HTMLElement>(`${TRIGGER}[aria-controls="${panel.id}"]`);
}

function hoveredTrigger(target: Element): HTMLElement | null {
  const trigger = target.closest<HTMLElement>(TRIGGER);
  if (trigger?.classList.contains("dpo-nav-trigger") && panelOf(trigger)) {
    return trigger;
  }
  const owner = triggerOfPanel(target.closest(".dpo-menu-panel"));
  return owner?.classList.contains("dpo-nav-trigger") ? owner : null;
}

function onPointerOver(event: PointerEvent): void {
  if (event.pointerType !== "mouse" || !canHover() || !(event.target instanceof Element)) {
    return;
  }
  const hovered = hoveredTrigger(event.target);
  if (clickClosed && clickClosed !== hovered) {
    clickClosed = null;
  }
  if (!hovered) {
    const opened = document.querySelector<HTMLElement>('.dpo-nav-trigger[aria-expanded="true"]');
    if (opened && !hoverTimer) {
      hoverTimer = window.setTimeout(() => {
        hoverTimer = 0;
        close(opened);
      }, HOVER_CLOSE_MS);
    }
    return;
  }
  cancelHoverClose();
  if (hovered !== clickClosed && !isOpen(hovered)) {
    open(hovered);
  }
}

function onClick(event: MouseEvent): void {
  const target = event.target instanceof Element ? event.target : null;
  const trigger = target?.closest<HTMLElement>(TRIGGER);
  if (trigger && panelOf(trigger)) {
    event.preventDefault();
    cancelHoverClose();
    if (isOpen(trigger)) {
      close(trigger);
      clickClosed = trigger;
    } else {
      open(trigger);
      clickClosed = null;
    }
    return;
  }
  if (!target?.closest(".dpo-menu-panel")) {
    closeAll(null);
  }
}

export function setupNavMenu(): void {
  document.addEventListener("pointerover", onPointerOver);
  document.addEventListener("pointerleave", (event) => {
    if (event.pointerType === "mouse") {
      cancelHoverClose();
      closeAll(null);
    }
  });
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
