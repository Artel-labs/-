import { prefersReducedMotion } from "./motion";

const REVEAL = "dpo-reveal";
const REVEAL_CARD = "dpo-reveal-card";
const VISIBLE = "dpo-in";
const CARD_STEP_MS = 36;
const CARD_GROUP = 6;
const CASCADE_STEP_MS = 70;
const CASCADE_MAX_MS = 280;
const FAILSAFE_MS = 700;
const SECTION_SELECTORS = ["section", ".card", "main section", "[data-reveal]"];
const CASCADE_SELECTOR = [
  ".dpo-explore-grid .explore-card",
  ".dpo-start",
  ".dpo-review",
  ".dpo-top5-grid > .dpo-tile",
  ".dpo-why-list > .dpo-why-row",
].join(", ");

function delay(element: HTMLElement, ms: number): void {
  element.style.setProperty("--dpo-delay", `${String(ms)}ms`);
}

function markTargets(): void {
  const seen = new Set<HTMLElement>();
  let cardIndex = 0;
  SECTION_SELECTORS.forEach((selector) => {
    document.querySelectorAll<HTMLElement>(selector).forEach((element) => {
      if (seen.has(element) || element.closest("header") || element.classList.contains("hero")) {
        return;
      }
      seen.add(element);
      element.classList.add(REVEAL);
      if (element.matches(".card")) {
        delay(element, (cardIndex % CARD_GROUP) * CARD_STEP_MS);
        cardIndex += 1;
      }
    });
  });
  document.querySelectorAll<HTMLElement>(CASCADE_SELECTOR).forEach((element) => {
    if (seen.has(element)) {
      return;
    }
    seen.add(element);
    element.classList.add(REVEAL, REVEAL_CARD);
    const index = element.parentElement ? [...element.parentElement.children].indexOf(element) : 0;
    delay(element, Math.min(index * CASCADE_STEP_MS, CASCADE_MAX_MS));
  });
}

function revealVisible(): boolean {
  const rest = document.querySelectorAll<HTMLElement>(`.${REVEAL}:not(.${VISIBLE})`);
  rest.forEach((element) => {
    const box = element.getBoundingClientRect();
    if (box.top < window.innerHeight && box.bottom > 0) {
      element.classList.add(VISIBLE);
    }
  });
  return rest.length > 0;
}

function observe(nodes: NodeListOf<HTMLElement>): void {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add(VISIBLE);
          observer.unobserve(entry.target);
        }
      });
    },
    { root: null, rootMargin: "0px 0px -6% 0px", threshold: 0.08 },
  );
  nodes.forEach((node) => {
    observer.observe(node);
  });
  const failsafe = window.setInterval(() => {
    if (!revealVisible()) {
      window.clearInterval(failsafe);
    }
  }, FAILSAFE_MS);
}

export function setupReveal(): void {
  markTargets();
  const nodes = document.querySelectorAll<HTMLElement>(`.${REVEAL}:not(.${VISIBLE})`);
  if (prefersReducedMotion()) {
    nodes.forEach((node) => node.classList.add(VISIBLE));
    return;
  }
  observe(nodes);
}
