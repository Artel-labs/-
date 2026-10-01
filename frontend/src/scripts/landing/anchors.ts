import { headerShift } from "./header-state";
import { prefersReducedMotion } from "./motion";

const HEADER_GAP_PX = 12;
const FOCUSABLE_TAGS = /^(a|button|input|select|textarea)$/i;

export function headerOffset(): number {
  const header = document.querySelector<HTMLElement>("header");
  return (header ? header.offsetHeight - headerShift() : 0) + HEADER_GAP_PX;
}

function scrollToTarget(target: Element): void {
  const top = target.getBoundingClientRect().top + window.scrollY - headerOffset();
  window.scrollTo({ top: Math.max(0, top), behavior: prefersReducedMotion() ? "auto" : "smooth" });
}

function targetOf(link: Element): HTMLElement | null {
  const id = link.getAttribute("href");
  if (!id || id.length < 2) {
    return null;
  }
  try {
    return document.querySelector<HTMLElement>(id);
  } catch {
    return null;
  }
}

function handleClick(event: MouseEvent): void {
  const link = event.target instanceof Element ? event.target.closest('a[href^="#"]') : null;
  if (!link || link.hasAttribute("data-application") || link.getAttribute("data-application-topic")) {
    return;
  }
  const target = targetOf(link);
  if (!target) {
    return;
  }
  event.preventDefault();
  scrollToTarget(target);
  if (!FOCUSABLE_TAGS.test(target.tagName) && !target.hasAttribute("tabindex")) {
    target.tabIndex = -1;
  }
  target.focus({ preventScroll: true });
  history.pushState(null, "", link.getAttribute("href"));
}

export function setupAnchors(): void {
  document.addEventListener("click", handleClick, { capture: true });
}
