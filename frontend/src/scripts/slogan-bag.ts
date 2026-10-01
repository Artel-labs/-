export interface Slogan {
  text: string;
  weight: number;
}

export interface BagState {
  bag: number[];
  last: number | null;
}

export interface Pick {
  index: number;
  state: BagState;
}

type Random = () => number;

const MIN_WEIGHT = 1;

export function shuffle<T>(items: readonly T[], random: Random): T[] {
  const out = [...items];
  for (let i = out.length - 1; i > 0; i -= 1) {
    const j = Math.floor(random() * (i + 1));
    [out[i], out[j]] = [out[j] as T, out[i] as T];
  }
  return out;
}

function weightOf(slogan: Slogan | undefined): number {
  const weight = Number(slogan?.weight);
  return Number.isFinite(weight) && weight >= MIN_WEIGHT ? Math.floor(weight) : MIN_WEIGHT;
}

export function fillBag(slogans: readonly Slogan[], random: Random): number[] {
  const indices = slogans.flatMap((slogan, index) => Array.from({ length: weightOf(slogan) }, () => index));
  return shuffle(indices, random);
}

function countsOf(flat: readonly number[]): Map<number, number> {
  const counts = new Map<number, number>();
  flat.forEach((index) => counts.set(index, (counts.get(index) ?? 0) + 1));
  return counts;
}

function interleavedSlots(size: number): number[] {
  const even = Array.from({ length: Math.ceil(size / 2) }, (_, i) => i * 2);
  const odd = Array.from({ length: Math.floor(size / 2) }, (_, i) => i * 2 + 1);
  return [...even, ...odd];
}

function avoidRepeat(bag: number[], last: number | null): number[] {
  if (bag[0] === last && bag.at(-1) !== last) {
    bag.reverse();
  }
  if (bag[0] === last) {
    const swap = bag.findIndex((index) => index !== last);
    if (swap > 0) {
      [bag[0], bag[swap]] = [bag[swap] as number, bag[0] as number];
    }
  }
  return bag;
}

export function drawBag(slogans: readonly Slogan[], last: number | null, random: Random): number[] {
  const flat = fillBag(slogans, random);
  if (flat.length < 2) {
    return flat;
  }
  const counts = countsOf(flat);
  const order = [...counts.keys()].sort((a, b) => (counts.get(b) ?? 0) - (counts.get(a) ?? 0));
  const slots = interleavedSlots(flat.length);
  const bag = new Array<number>(flat.length);
  let at = 0;
  order.forEach((index) => {
    for (let k = 0; k < (counts.get(index) ?? 0); k += 1) {
      bag[slots[at] as number] = index;
      at += 1;
    }
  });
  return avoidRepeat(bag, last);
}

function isIndex(value: unknown, size: number): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0 && value < size;
}

export function next(slogans: readonly Slogan[], state: Partial<BagState> | null, random: Random = Math.random): Pick {
  const size = slogans.length;
  if (!size) {
    return { index: -1, state: { bag: [], last: null } };
  }
  const saved = Array.isArray(state?.bag) ? state.bag.filter((value) => isIndex(value, size)) : [];
  const last = isIndex(state?.last, size) ? state.last : null;
  const bag = saved.length ? saved : drawBag(slogans, last, random);
  const index = bag.shift() ?? -1;
  return { index, state: { bag, last: index } };
}
