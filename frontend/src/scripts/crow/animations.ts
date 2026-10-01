import { bell, blinkAt, clamp, ease, outCubic, talk, TAU } from "./motion";
import type { Pose } from "./pose";

export interface Animation {
  dur: number;
  loop: boolean;
  track?: boolean;
  bubble?: [number, number];
  text?: string;
  fn: (t: number, p: Pose) => void;
}

const WALK_ACROSS_START = 300;
const WALK_ACROSS_DISTANCE = 900;
export const WALK_ACROSS_END = WALK_ACROSS_START - WALK_ACROSS_DISTANCE;

function idle(t: number, p: Pose): void {
  p.cy = Math.sin(t * 1.7) * 3.5;
  p.csy = 1 + Math.sin(t * 1.7) * 0.007;
  p.csx = 1 - Math.sin(t * 1.7) * 0.007;
  p.crot = Math.sin(t * 0.75) * 0.5;
  p.hrot = Math.sin(t * 0.72 + 1.1) * 1.3;
  p.hy = Math.sin(t * 1.7 + 0.4) * 2.6;
  p.arot = Math.sin(t * 0.95) * 1.6;
  p.blink = blinkAt(t, 4.1);
}

function walk(t: number, p: Pose): void {
  const phase = (t / 0.92) * TAU;
  const step = Math.abs(Math.sin(phase));
  p.cy = -step * 9 + 3;
  p.crot = Math.sin(phase) * 2.2;
  p.llrot = Math.sin(phase) * 10;
  p.lrrot = Math.sin(phase + Math.PI) * 10;
  p.csx = 1 + step * 0.006;
  p.csy = 1 - step * 0.006;
  p.hy = -Math.abs(Math.sin(phase + 0.45)) * 4 + 1.5;
  p.hrot = Math.sin(phase + 0.85) * 3;
  p.hx = Math.sin(phase) * 4;
  p.arot = Math.sin(phase + Math.PI) * 10;
  p.blink = blinkAt(t, 3.3);
}

function walkAcross(t: number, p: Pose): void {
  walk(t, p);
  p.rx = WALK_ACROSS_START - (t / 5.4) * WALK_ACROSS_DISTANCE;
}

function runIn(t: number, p: Pose): void {
  const run = clamp(t / 1.1, 0, 1);
  const phase = (t / 0.36) * TAU;
  p.rx = -640 * (1 - outCubic(run));
  if (t < 1.1) {
    p.llrot = Math.sin(phase) * 15;
    p.lrrot = Math.sin(phase + Math.PI) * 15;
    p.cy = -Math.abs(Math.sin(phase)) * 15;
    p.crot = -7 + Math.sin(phase) * 2.4;
    p.arot = -15 + Math.sin(phase + Math.PI) * 20;
    p.hrot = -2.5;
    p.hy = -3;
    return;
  }
  const settle = 1 - ease(clamp((t - 1.1) / 1.0, 0, 1));
  p.rx = 30 * bell(clamp((t - 1.1) / 0.55, 0, 1));
  p.crot = -7 * settle + 7 * bell(clamp((t - 1.1) / 0.7, 0, 1)) * settle;
  p.llrot = 14 * settle;
  p.lrrot = -11 * settle;
  p.cy = -5 * settle + Math.sin(t * 12) * 2 * settle;
  p.arot = -12 * settle;
  p.hrot = -2.5 * settle + Math.sin((t - 1.1) * 10) * 2 * settle;
  p.blink = blinkAt(t - 1.5, 2.2);
}

function nod(t: number, p: Pose): void {
  idle(t, p);
  const envelope = t < 1.35 ? Math.pow(bell(t / 1.35), 0.55) : 0;
  const swing = (1 - Math.cos(t * 8.6)) / 2;
  p.hy += swing * 17 * envelope;
  p.hrot += -swing * 2 * envelope;
  p.cy += swing * 3 * envelope;
}

function shake(t: number, p: Pose): void {
  idle(t, p);
  const envelope = t < 1.5 ? Math.pow(bell(t / 1.5), 0.5) : 0;
  p.hrot += Math.sin(t * 10.5) * 2.4 * envelope;
  p.hx += Math.sin(t * 10.5) * 11 * envelope;
  p.ex += Math.sin(t * 10.5) * 2 * envelope;
}

function wave(t: number, p: Pose): void {
  idle(t, p);
  const u = ease(t / 0.34) - ease((t - 1.95) / 0.45);
  p.arot += -26 * u + Math.sin(t * 9.5) * 11 * u;
  p.ay += -16 * u;
  p.ax += 8 * u;
  p.hrot += -3 * u;
  p.crot += -1.3 * u;
}

function inspect(t: number, p: Pose): void {
  idle(t * 0.6, p);
  const u = ease(t / 0.65) - ease((t - 3.4) / 0.6);
  const scan = Math.sin(t * 1.5);
  p.arot += (-11 + scan * 3) * u;
  p.ay += -54 * u;
  p.ax += 40 * u;
  p.hrot += (-9 + scan * 1.8) * u;
  p.hx += -16 * u;
  p.hy += 18 * u;
  p.ex += -4 * u;
  p.ey += 3 * u;
}

function point(t: number, p: Pose): void {
  idle(t * 0.7, p);
  const u = ease(t / 0.42) - ease((t - 2.3) / 0.5);
  const jab = t > 0.5 && t < 1.7 ? Math.sin((t - 0.5) * 8) : 0;
  p.arot += (-38 + jab * 5) * u;
  p.ay += -26 * u;
  p.ax += -8 * u;
  p.hrot += -7 * u;
  p.crot += -2 * u;
  p.ex += -2 * u;
}

function jump(t: number, p: Pose): void {
  let squash = 0;
  let height = 0;
  if (t < 0.34) {
    squash = bell(t / 0.34);
  }
  if (t >= 0.34 && t < 1.08) {
    height = bell((t - 0.34) / 0.74);
  }
  if (t >= 1.08 && t < 1.5) {
    squash = bell((t - 1.08) / 0.42) * 0.8;
  }
  p.ry = -height * 155;
  p.csy = 1 - squash * 0.11 + height * 0.05;
  p.csx = 1 + squash * 0.09 - height * 0.04;
  p.cy = squash * 15;
  p.llrot = -height * 13 + squash * 6;
  p.lrrot = height * 13 - squash * 6;
  p.arot = -height * 32 + squash * 13;
  p.hy = -height * 9 + squash * 6;
  p.hrot = height * 4;
  p.beak = height * 0.55;
  p.blink = blinkAt(t + 1.4, 3);
}

function think(t: number, p: Pose): void {
  idle(t * 0.55, p);
  const u = ease(t / 0.7) - ease((t - 3.8) / 0.7);
  p.hrot += 8.5 * u;
  p.hx += 5 * u;
  p.arot += -11 * u;
  p.ay += -32 * u;
  p.ax += 30 * u;
  p.ey += -5 * u;
  p.ex += 3 * u;
  p.cy += Math.sin(t * 1.25) * 2.2 * u;
}

function leave(t: number, p: Pose): void {
  if (t < 0.8) {
    idle(t, p);
    const u = bell(t / 0.8);
    p.arot += -25 * u;
    p.ay += -13 * u;
    p.hrot += -3 * u;
    return;
  }
  walk(t - 0.8, p);
  p.rx = -600 * ease((t - 0.8) / 2.1);
  p.op = 1 - clamp((t - 2.4) / 0.9, 0, 1);
}

function helpQ(t: number, p: Pose): void {
  idle(t, p);
  const u = ease((t - 0.15) / 0.32) - ease((t - 2.3) / 0.45);
  p.arot += -20 * u + Math.sin(t * 8.4) * 6 * u;
  p.ay += -11 * u;
  p.beak = talk(t - 0.55, 1.15);
  p.hy += Math.sin((t - 0.55) * 14) * 2 * (t > 0.55 && t < 1.7 ? 1 : 0);
  p.hrot += -2.2 * u;
}

function askQ(t: number, p: Pose): void {
  idle(t, p);
  const u = ease((t - 0.1) / 0.35) - ease((t - 2.5) / 0.5);
  p.hrot += 7 * u;
  p.hx += 4 * u;
  p.beak = talk(t - 0.5, 1.25);
  p.arot += -9 * u;
  p.ay += -8 * u;
  p.cy += -3 * u;
  p.ey += -3 * u;
}

export const ANIMATIONS = {
  idle: { dur: 6, loop: true, fn: idle },
  walk: { dur: 0.92, loop: true, fn: walk },
  walkAcross: { dur: 5.4, loop: true, track: false, fn: walkAcross },
  runIn: { dur: 2.5, loop: false, fn: runIn },
  nod: { dur: 1.9, loop: false, fn: nod },
  shake: { dur: 2.1, loop: false, fn: shake },
  wave: { dur: 2.6, loop: false, fn: wave },
  inspect: { dur: 4.2, loop: true, track: false, fn: inspect },
  point: { dur: 3, loop: false, fn: point },
  jump: { dur: 2, loop: false, fn: jump },
  think: { dur: 4.6, loop: true, fn: think },
  leave: { dur: 3.5, loop: false, fn: leave },
  helpQ: { dur: 4.6, loop: false, bubble: [0.5, 3.9], text: "Чем помочь?", fn: helpQ },
  askQ: { dur: 4.6, loop: false, bubble: [0.45, 3.9], text: "Есть вопросы?", fn: askQ },
  invite: { dur: 999, loop: false, bubble: [0.15, 998], text: "Подсказать?", fn: idle },
} satisfies Record<string, Animation>;

export type AnimationName = keyof typeof ANIMATIONS;

export function sayAnimation(text: string): Animation {
  return { dur: 4.6, loop: false, bubble: [0.45, 3.9], text, fn: helpQ };
}
