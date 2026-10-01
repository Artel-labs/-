export interface Pose {
  rx: number;
  ry: number;
  flip: number;
  op: number;
  cy: number;
  crot: number;
  csx: number;
  csy: number;
  hx: number;
  hy: number;
  hrot: number;
  ax: number;
  ay: number;
  arot: number;
  llrot: number;
  lrrot: number;
  ex: number;
  ey: number;
  blink: number;
  beak: number;
  track: number;
}

export type PoseKey = keyof Pose;

export function restPose(): Pose {
  return {
    rx: 0,
    ry: 0,
    flip: 1,
    op: 1,
    cy: 0,
    crot: 0,
    csx: 1,
    csy: 1,
    hx: 0,
    hy: 0,
    hrot: 0,
    ax: 0,
    ay: 0,
    arot: 0,
    llrot: 0,
    lrrot: 0,
    ex: 0,
    ey: 0,
    blink: 0,
    beak: 0,
    track: 1,
  };
}

export function blendPoses(from: Pose, to: Pose, k: number): Pose {
  const pose = restPose();
  (Object.keys(to) as PoseKey[]).forEach((key) => {
    pose[key] = from[key] * (1 - k) + to[key] * k;
  });
  return pose;
}
