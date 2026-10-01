const GAP_PX = 12;
const BOTTOM_BARS = [".dpo-mobile-cta", ".mobile-cta", ".buy-bar", ".cmp-bar.is-open"];
const LIFTED = ["body>.crow-mascot", ".crow-hit-btn", "#crow-vi-btn"];

function topOf(element: Element | null): number | null {
  if (!element) {
    return null;
  }
  const rect = element.getBoundingClientRect();
  return rect.height ? rect.top : null;
}

function bottomValue(): string {
  const tops = [document.getElementById("cookieBanner"), ...BOTTOM_BARS.map((selector) => document.querySelector(selector))]
    .map(topOf)
    .filter((top): top is number => top !== null);
  if (!tops.length) {
    return "";
  }
  const overlap = window.innerHeight - Math.min(...tops);
  return `calc(${String(Math.max(0, overlap + GAP_PX))}px + env(safe-area-inset-bottom, 0px))`;
}

export function keepAboveBars(panel: HTMLElement | null): void {
  const value = bottomValue();
  LIFTED.forEach((selector) => {
    const element = document.querySelector<HTMLElement>(selector);
    if (element) {
      element.style.bottom = value;
    }
  });
  if (panel) {
    panel.style.bottom = value;
  }
}
