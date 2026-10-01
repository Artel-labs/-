import { headerOffset } from "./anchors";
import { onFrame } from "./motion";

const ACTIVE_CLASS = "is-active";
const LOOK_AHEAD_PX = 48;
const BOTTOM_TOLERANCE_PX = 24;
const LINK_SELECTOR = 'header nav:not(.dpo-mobile-nav) a[href^="#"]:not(.btn):not([class*="btn-"])';

interface Target {
  link: HTMLAnchorElement;
  section: HTMLElement;
}

function targets(): Target[] {
  return [...document.querySelectorAll<HTMLAnchorElement>(LINK_SELECTOR)]
    .filter((link) => !link.closest(".dpo-mobile-panel"))
    .flatMap((link) => {
      const section = document.querySelector<HTMLElement>(link.getAttribute("href") ?? "");
      return section ? [{ link, section }] : [];
    });
}

function currentSection(zones: HTMLElement[]): HTMLElement | null {
  const line = window.scrollY + headerOffset() + LOOK_AHEAD_PX;
  return zones.reduce<HTMLElement | null>(
    (found, zone) => (zone.offsetTop <= line && (!found || zone.offsetTop >= found.offsetTop) ? zone : found),
    null,
  );
}

function nearBottom(): boolean {
  return window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - BOTTOM_TOLERANCE_PX;
}

export function setupActiveNav(): void {
  const items = targets();
  if (!items.length) {
    return;
  }
  const zones = [...new Set([...document.querySelectorAll<HTMLElement>("section[id]"), ...items.map((item) => item.section)])];
  const sync = (): void => {
    const zone = currentSection(zones);
    const current = nearBottom() ? items.at(-1) : items.find((item) => item.section === zone);
    items.forEach((item) => {
      item.link.classList.toggle(ACTIVE_CLASS, item === current);
    });
  };
  const schedule = onFrame(sync);
  window.addEventListener("scroll", schedule, { passive: true });
  window.addEventListener("resize", schedule, { passive: true });
  sync();
}
