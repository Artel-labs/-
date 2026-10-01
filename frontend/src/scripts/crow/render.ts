import type { Animation } from "./animations";
import { clamp, ease } from "./motion";
import type { Pose } from "./pose";
import type { Parts } from "./rig";

const RIG_WIDTH = 1400;
const RIG_HEIGHT = 1465;
const ARM_WIDTH = 259;
const ARM_HEIGHT = 429;
const EYE_WIDTH = 88;
const EYE_HEIGHT = 135;

function percent(value: number, base: number): string {
  return ((value / base) * 100).toFixed(3);
}

function deg(value: number): string {
  return value.toFixed(2);
}

function headTransform(p: Pose): string {
  return `translate(${percent(p.hx, RIG_WIDTH)}%,${percent(p.hy, RIG_HEIGHT)}%) rotate(${deg(p.hrot)}deg)`;
}

function eyeTransform(p: Pose): string {
  return `translate(${percent(p.ex, EYE_WIDTH)}%,${percent(p.ey, EYE_HEIGHT)}%) scaleY(${(1 - p.blink * 0.92).toFixed(3)})`;
}

function renderShadow(parts: Parts, p: Pose): void {
  const scale = 1 - clamp(-p.ry / 420, 0, 0.45);
  parts.shadow.style.transform = `scale(${scale.toFixed(3)})`;
  parts.shadow.style.opacity = (0.16 * scale * p.op).toFixed(3);
}

export function renderPose(parts: Parts, p: Pose): void {
  parts.root.style.transform = `translate(${percent(p.rx, RIG_WIDTH)}%,${percent(p.ry, RIG_HEIGHT)}%) scaleX(${String(p.flip)})`;
  parts.root.style.opacity = String(p.op);
  parts.char.style.transform = `translate(0,${percent(p.cy, RIG_HEIGHT)}%) rotate(${deg(p.crot)}deg) scale(${p.csx.toFixed(4)},${p.csy.toFixed(4)})`;
  parts.head.style.transform = headTransform(p);
  parts.jaw.style.transform = headTransform(p);
  parts.arm.style.transform = `translate(${percent(p.ax, ARM_WIDTH)}%,${percent(p.ay, ARM_HEIGHT)}%) rotate(${deg(p.arot)}deg)`;
  parts.legL.style.transform = `rotate(${deg(p.llrot)}deg)`;
  parts.legR.style.transform = `rotate(${deg(p.lrrot)}deg)`;
  parts.eyeL.style.transform = eyeTransform(p);
  parts.eyeR.style.transform = eyeTransform(p);
  parts.beak.style.transform = `rotate(${deg(p.beak * -6.5)}deg)`;
  renderShadow(parts, p);
}

export function offsetPx(p: Pose, width: number): number {
  return (p.rx / RIG_WIDTH) * width;
}

function bubbleVisibility(animation: Animation, t: number): number {
  if (!animation.bubble) {
    return 0;
  }
  const [from, to] = animation.bubble;
  return ease((t - from) / 0.26) - ease((t - to) / 0.3);
}

export function renderBubble(parts: Parts, animation: Animation, t: number, offset: number): void {
  const v = bubbleVisibility(animation, t);
  if (animation.text && v > 0.01 && parts.bubbleText.textContent !== animation.text) {
    parts.bubbleText.textContent = animation.text;
  }
  parts.bubble.style.opacity = v.toFixed(3);
  parts.bubble.style.transform = `translateX(${offset.toFixed(2)}px) translateY(${((1 - v) * 10).toFixed(2)}px) scale(${(0.72 + 0.28 * v).toFixed(3)})`;
}

export const RIG_ASPECT = RIG_HEIGHT / RIG_WIDTH;
