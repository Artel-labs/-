const RUBBER_DIMENSION = 300;
const RUBBER_COEFFICIENT = 0.55;
const MAX_FRAME_MS = 32;
const SETTLE_DISTANCE = 0.5;
const SETTLE_VELOCITY = 20;
const VELOCITY_SAMPLES = 6;
const VELOCITY_WINDOW_MS = 100;
const DECELERATION = 0.998;
const MS_PER_SECOND = 1000;

interface Sample {
  time: number;
  position: number;
}

export function rubberBand(overshoot: number): number {
  return (overshoot * RUBBER_DIMENSION * RUBBER_COEFFICIENT) / (RUBBER_DIMENSION + RUBBER_COEFFICIENT * Math.abs(overshoot));
}

export function projectedPosition(position: number, velocity: number): number {
  return position + ((velocity / MS_PER_SECOND) * DECELERATION) / (1 - DECELERATION);
}

export class VelocityTracker {
  private samples: Sample[] = [];

  start(time: number, position: number): void {
    this.samples = [{ time, position }];
  }

  add(time: number, position: number): void {
    this.samples.push({ time, position });
    while (this.samples.length > VELOCITY_SAMPLES || time - (this.samples[0]?.time ?? time) > VELOCITY_WINDOW_MS) {
      this.samples.shift();
    }
  }

  velocity(): number {
    const first = this.samples[0];
    const last = this.samples.at(-1);
    if (!first || !last || last.time <= first.time) {
      return 0;
    }
    return ((last.position - first.position) / (last.time - first.time)) * MS_PER_SECOND;
  }
}

export class Spring {
  position = 0;
  velocity = 0;
  private frame = 0;

  constructor(private readonly render: (position: number) => void) {}

  set(position: number): void {
    this.position = position;
    this.render(position);
  }

  stop(): void {
    if (this.frame) {
      window.cancelAnimationFrame(this.frame);
      this.frame = 0;
    }
  }

  animate(target: number, response: number, onSettle: () => void): void {
    const stiffness = ((2 * Math.PI) / response) ** 2;
    const damping = 2 * Math.sqrt(stiffness);
    let previous = performance.now();
    this.stop();
    const step = (now: number): void => {
      const dt = Math.min(MAX_FRAME_MS, now - previous) / MS_PER_SECOND;
      previous = now;
      this.velocity += (stiffness * (target - this.position) - damping * this.velocity) * dt;
      this.set(this.position + this.velocity * dt);
      if (Math.abs(target - this.position) < SETTLE_DISTANCE && Math.abs(this.velocity) < SETTLE_VELOCITY) {
        this.set(target);
        this.frame = 0;
        onSettle();
        return;
      }
      this.frame = window.requestAnimationFrame(step);
    };
    this.frame = window.requestAnimationFrame(step);
  }
}

export function prefersTouchMotion(): boolean {
  return window.matchMedia("(pointer: coarse)").matches && !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}
