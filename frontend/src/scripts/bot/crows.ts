import { launcherCrow } from "../crow/launcher";
import { CrowMascot } from "../crow/mascot";

const HEAD_WIDTH = 56;
const LEAVE_MS = 1200;

export const reducedMotion = (): boolean => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

let leaveTimer = 0;

function hitButton(): HTMLElement | null {
  return document.querySelector<HTMLElement>(".crow-hit-btn");
}

export function sendLauncherAway(): void {
  const hit = hitButton();
  if (hit) {
    hit.style.pointerEvents = "none";
  }
  const crow = launcherCrow();
  if (!crow) {
    return;
  }
  window.clearTimeout(leaveTimer);
  if (reducedMotion()) {
    crow.hide();
    return;
  }
  crow.play("leave");
  leaveTimer = window.setTimeout(() => {
    crow.hide();
  }, LEAVE_MS);
}

export function bringLauncherBack(): void {
  window.clearTimeout(leaveTimer);
  const hit = hitButton();
  if (hit) {
    hit.style.pointerEvents = "";
  }
  const crow = launcherCrow();
  if (!crow) {
    return;
  }
  crow.show();
  if (!reducedMotion()) {
    crow.play("runIn");
  }
}

export function mountHeadCrow(slot: HTMLElement): CrowMascot {
  const crow = new CrowMascot({ anchor: slot, width: HEAD_WIDTH, zIndex: 1, solo: false, idleSeconds: 0 });
  if (!reducedMotion()) {
    crow.play("wave");
  }
  return crow;
}
