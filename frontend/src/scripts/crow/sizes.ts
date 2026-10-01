import { RIG_ASPECT } from "./render";

const NARROW_QUERY = "(max-width: 1023px)";
const WIDE_WIDTH = 160;
const NARROW_WIDTH = 96;
const WIDE_EDGE = 24;
const NARROW_EDGE = 8;

export function isNarrow(): boolean {
  return window.matchMedia(NARROW_QUERY).matches;
}

export function slotWidth(): number {
  return isNarrow() ? NARROW_WIDTH : WIDE_WIDTH;
}

export function slotHeight(width: number): number {
  return Math.round(width * RIG_ASPECT);
}

export function edgeOffset(): number {
  return isNarrow() ? NARROW_EDGE : WIDE_EDGE;
}
