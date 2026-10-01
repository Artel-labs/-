import data from "../data/slogans.json";
import { next, type BagState } from "./slogan-bag";

const BAG_KEY = `dpo.slogan.bag.v${String(data.version)}`;
const LAST_KEY = `dpo.slogan.last.v${String(data.version)}`;

function read(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function write(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    return;
  }
}

function savedState(): Partial<BagState> | null {
  try {
    const bag: unknown = JSON.parse(read(BAG_KEY) ?? "null");
    const last = read(LAST_KEY);
    return { bag: Array.isArray(bag) ? bag.filter((item): item is number => typeof item === "number") : [], last: last === null ? null : Number(last) };
  } catch {
    return null;
  }
}

export function showMotto(): void {
  const picked = next(data.slogans, savedState());
  const text = data.slogans[picked.index]?.text;
  if (!text) {
    return;
  }
  write(BAG_KEY, JSON.stringify(picked.state.bag));
  write(LAST_KEY, String(picked.state.last));
  document.querySelectorAll("[data-dpo-motto]").forEach((node) => {
    node.textContent = text;
  });
}
