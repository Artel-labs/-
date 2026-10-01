import { CrowMascot } from "./mascot";
import { slotWidth } from "./sizes";

const INLINE_LIVE_CLASS = "crow-inline-live";
const VI_MODE_CLASS = "vi-mode";
const SKIP_WALK_QUERY = "(max-width:600px)";
const VISIBLE_SHARE = 0.3;

interface WalkIn {
  crow: CrowMascot;
  hit: HTMLButtonElement;
}

function hitButton(): HTMLButtonElement {
  const hit = document.createElement("button");
  hit.type = "button";
  hit.className = "crow-walk-hit";
  hit.dataset.botOpen = "";
  hit.setAttribute("aria-label", "Открыть поддержку");
  return hit;
}

export function mountWalkIn(slot: HTMLElement): void {
  const width = slotWidth();
  let current: WalkIn | null = null;

  const teardown = (): void => {
    if (!current) {
      return;
    }
    current.crow.destroy();
    current.hit.remove();
    current = null;
    document.documentElement.classList.remove(INLINE_LIVE_CLASS);
  };

  const spawn = (): void => {
    if (current || document.documentElement.classList.contains(VI_MODE_CLASS)) {
      return;
    }
    const crow = new CrowMascot({ anchor: slot, align: "right", width, followCursor: false, idleSeconds: 0, solo: false, onClick: () => undefined });
    const hit = hitButton();
    hit.addEventListener("click", teardown);
    slot.append(hit);
    current = { crow, hit };
    document.documentElement.classList.add(INLINE_LIVE_CLASS);
    crow.walkIn(window.matchMedia(SKIP_WALK_QUERY).matches);
  };

  new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          spawn();
        } else {
          teardown();
        }
      });
    },
    { threshold: VISIBLE_SHARE },
  ).observe(slot);
}

export function setupWalkIn(): void {
  const mount = (): void => {
    const slot = document.querySelector<HTMLElement>("[data-crow-walk]");
    if (slot) {
      mountWalkIn(slot);
    }
  };
  if (document.readyState === "complete") {
    mount();
  } else {
    window.addEventListener("load", mount, { once: true });
  }
}
