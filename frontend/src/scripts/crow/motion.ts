export const TAU = Math.PI * 2;

export function clamp(value: number, min: number, max: number): number {
  return value < min ? min : value > max ? max : value;
}

export function ease(t: number): number {
  const x = clamp(t, 0, 1);
  return x * x * (3 - 2 * x);
}

export function outCubic(t: number): number {
  return 1 - Math.pow(1 - clamp(t, 0, 1), 3);
}

export function bell(t: number): number {
  return Math.sin(Math.PI * clamp(t, 0, 1));
}

export function blinkAt(t: number, period: number): number {
  const phase = ((t % period) + period) % period;
  const duration = 0.12;
  if (phase < duration) {
    return Math.sin(Math.PI * (phase / duration));
  }
  if (phase > 0.26 && phase < 0.26 + duration && Math.floor(t / period) % 3 === 0) {
    return Math.sin(Math.PI * ((phase - 0.26) / duration));
  }
  return 0;
}

export function talk(t: number, duration: number): number {
  if (t < 0 || t > duration) {
    return 0;
  }
  const envelope = Math.min(1, t / 0.1) * Math.min(1, (duration - t) / 0.12);
  const wave = 0.5 + 0.5 * Math.sin(t * 15.5);
  return Math.pow(wave, 0.75) * (0.55 + 0.45 * Math.abs(Math.sin(t * 3.4))) * envelope;
}
