import { onFrame } from "./motion";

const SCROLLED_AFTER_PX = 120;
const RESYNC_DELAY_MS = 200;
const HEADER_VARIABLE = "--dpo-header-h";
const SHIFT_VARIABLE = "--hdr-shift";
const SCROLLED_CLASS = "dpo-scrolled";

export function headerShift(): number {
  return parseFloat(getComputedStyle(document.documentElement).getPropertyValue(SHIFT_VARIABLE)) || 0;
}

export function syncHeaderHeight(): void {
  const header = document.querySelector("header");
  if (!header) {
    return;
  }
  const height = Math.round(header.getBoundingClientRect().height - headerShift());
  if (height > 0) {
    document.documentElement.style.setProperty(HEADER_VARIABLE, `${String(height)}px`);
  }
}

function syncScrolled(): void {
  const scrolled = window.scrollY > SCROLLED_AFTER_PX;
  const root = document.documentElement;
  if (root.classList.contains(SCROLLED_CLASS) !== scrolled) {
    root.classList.toggle(SCROLLED_CLASS, scrolled);
    window.setTimeout(syncHeaderHeight, RESYNC_DELAY_MS);
  }
}

export function setupHeaderState(): void {
  window.addEventListener("resize", syncHeaderHeight);
  window.addEventListener("scroll", onFrame(syncScrolled), { passive: true });
  syncScrolled();
  syncHeaderHeight();
  void document.fonts.ready.then(syncHeaderHeight);
}
