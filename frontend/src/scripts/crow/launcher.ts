import { CrowMascot } from "./mascot";
import { edgeOffset, slotHeight, slotWidth } from "./sizes";

const IDLE_TIMEOUT_MS = 3500;
const IDLE_FALLBACK_MS = 1200;
const LAUNCHER_Z_INDEX = 920;
const LAUNCHER_IDLE_SECONDS = 14;
const WAKE_EVENTS = ["pointerdown", "keydown", "scroll", "touchstart"] as const;

let pageCrow: CrowMascot | null = null;

export function launcherCrow(): CrowMascot | null {
  return pageCrow;
}

function supportButton(): HTMLButtonElement {
  const node = document.createElement("button");
  node.type = "button";
  node.dataset.botOpen = "";
  return node;
}

function hitButton(): HTMLButtonElement {
  const hit = supportButton();
  hit.className = "crow-hit-btn";
  const label = document.createElement("span");
  label.className = "visually-hidden";
  label.textContent = "Открыть поддержку";
  hit.append(label);
  return hit;
}

function viButton(): HTMLButtonElement {
  const node = supportButton();
  node.id = "crow-vi-btn";
  node.textContent = "Поддержка";
  return node;
}

function setSizes(width: number): void {
  const root = document.documentElement.style;
  root.setProperty("--crow-edge", `${String(edgeOffset())}px`);
  root.setProperty("--crow-hit-width", `${String(width)}px`);
  root.setProperty("--crow-hit-height", `${String(slotHeight(width))}px`);
}

function mount(): void {
  if (pageCrow) {
    return;
  }
  const width = slotWidth();
  setSizes(width);
  document.body.append(hitButton(), viButton());
  pageCrow = new CrowMascot({
    anchor: "bottom-right",
    width,
    zIndex: LAUNCHER_Z_INDEX,
    idleSeconds: LAUNCHER_IDLE_SECONDS,
    idleAnim: document.getElementById("filters") ? "helpQ" : "askQ",
  });
}

function whenIdle(callback: () => void): void {
  let ran = false;
  const run = (): void => {
    if (ran) {
      return;
    }
    ran = true;
    callback();
  };
  if (typeof window.requestIdleCallback === "function") {
    window.requestIdleCallback(run, { timeout: IDLE_TIMEOUT_MS });
  } else {
    window.setTimeout(run, IDLE_FALLBACK_MS);
  }
  WAKE_EVENTS.forEach((name) => {
    window.addEventListener(name, run, { once: true, passive: true });
  });
}

export function setupCrowLauncher(): void {
  const start = (): void => {
    whenIdle(mount);
  };
  if (document.readyState === "complete") {
    start();
  } else {
    window.addEventListener("load", start, { once: true });
  }
}
