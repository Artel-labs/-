import { byStart, normalize, parseQuery, sameStem, search, stem, type SearchProgram, type SearchResult } from "./match.ts";
import type { BotData, BotProgram, FaqEntry, FaqGap } from "./types";

export type Intent = "priceRange" | "upcomingStarts" | "pickProgram";

export type Reply =
  | { kind: "programs"; intro: string; programs: BotProgram[] }
  | { kind: "programs-weak"; programs: BotProgram[] }
  | { kind: "duration"; text: string; anchor: string; extra?: BotProgram[] }
  | { kind: "answer"; answer: FaqEntry; extra?: BotProgram[] }
  | { kind: "gap"; gap: FaqGap }
  | { kind: "none"; programs: BotProgram[] };

interface Classified {
  primary?: { intro: string; programs: BotProgram[] };
  forExtra?: BotProgram[];
  weak?: BotProgram[];
}

interface Duration {
  raw: string;
  num: string;
  root: string;
  days: number;
}

const MIN_TOKEN = 2;
const SHOWN_PROGRAMS = 5;
const NONE_PROGRAMS = 3;
const DAYS_IN: Record<string, number> = { недел: 7, месяц: 30, год: 365 };
const INTENT_TRIGGERS: [Intent, string[]][] = [
  ["priceRange", ["сколько стоит", "цена"]],
  ["upcomingStarts", ["ближайший старт", "когда старт"]],
  ["pickProgram", ["подобрать программу"]],
];

export function tokenize(text: string): string[] {
  return normalize(text)
    .replace(/[^а-яa-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((word) => word.length >= MIN_TOKEN && !/^\d+$/.test(word))
    .map(stem);
}

function tokenMatchesAny(token: string, queryTokens: string[]): boolean {
  return queryTokens.some((candidate) => sameStem(token, candidate));
}

export function triggerMatches(trigger: string, queryTokens: string[]): boolean {
  const tokens = tokenize(trigger);
  return tokens.length > 0 && tokens.every((token) => tokenMatchesAny(token, queryTokens));
}

export function findByTriggers<T extends { triggers: string[] }>(queryTokens: string[], list: T[]): T | null {
  return list.find((item) => item.triggers.some((trigger) => triggerMatches(trigger, queryTokens))) ?? null;
}

function durationRoot(word: string): string {
  if (word.startsWith("недел")) {
    return "недел";
  }
  if (word.startsWith("месяц")) {
    return "месяц";
  }
  return /^(год|лет)/.test(word) ? "год" : word;
}

function parseDuration(raw: string): Duration | null {
  const found = /^(\d+(?:,\d+)?)\s+(\S+)/.exec(raw.trim());
  if (!found) {
    return null;
  }
  const [, num = "", word = ""] = found;
  const root = durationRoot(word);
  return { raw: raw.trim(), num, root, days: parseFloat(num.replace(",", ".")) * (DAYS_IN[root] ?? 1) };
}

function durationRange(programs: BotProgram[], type: string): string | null {
  const items = programs
    .filter((program) => program.type === type && program.duration)
    .map((program) => parseDuration(program.duration ?? ""))
    .filter((item): item is Duration => item !== null);
  const [first] = items;
  if (!first) {
    return null;
  }
  const min = items.reduce((low, item) => (item.days < low.days ? item : low), first);
  const max = items.reduce((high, item) => (item.days > high.days ? item : high), first);
  if (min.raw === max.raw) {
    return min.raw;
  }
  return min.root === max.root ? `${min.num} – ${max.raw}` : `${min.raw} – ${max.raw}`;
}

export function durationText(programs: BotProgram[]): string {
  const qualification = durationRange(programs, "ПК");
  const retraining = durationRange(programs, "ПП");
  return [
    ...(qualification ? [`Повышение квалификации: длительность обычно ${qualification}.`] : []),
    ...(retraining ? [`Профессиональная переподготовка: длительность обычно ${retraining}.`] : []),
  ].join("\n");
}

export function upcoming<T extends SearchProgram>(programs: T[], count: number): T[] {
  return [...programs].sort(byStart).slice(0, count);
}

export function priceRange(programs: BotProgram[]): { min: number; max: number } | null {
  const prices = programs.map((program) => program.price).filter((price): price is number => typeof price === "number");
  return prices.length ? { min: Math.min(...prices), max: Math.max(...prices) } : null;
}

export function formatPrice(amount: number): string {
  return `${String(amount).replace(/\B(?=(\d{3})+(?!\d))/g, " ")} ₽`;
}

export function sphereList(programs: BotProgram[]): string[] {
  return [...new Set(programs.map((program) => program.sphere).filter(Boolean))];
}

export function pickBy(programs: BotProgram[], field: "sphere" | "type", value: string): BotProgram[] {
  return programs.filter((program) => program[field] === value);
}

export function introFor(reason: string, count: number): string {
  if (reason === "filter") {
    return "Отобрала по вашим условиям:";
  }
  return count === 1 ? "Нашла одну программу:" : "Вот что нашла:";
}

export function titleHit(stems: string[], title: string): boolean {
  const titleWords = tokenize(title);
  return stems.some((candidate) => titleWords.some((word) => sameStem(candidate, word)));
}

export function classifySearch(found: SearchResult<BotProgram>, stems: string[]): Classified {
  if (found.reason === "empty" || found.reason === "none") {
    return {};
  }
  if (found.reason === "filter") {
    return { primary: { intro: introFor("filter", found.programs.length), programs: found.programs } };
  }
  const strong = found.programs.filter((program) => titleHit(stems, program.title));
  if (strong.length) {
    return { primary: { intro: introFor(found.reason, strong.length), programs: strong }, forExtra: strong };
  }
  return { weak: found.programs };
}

function extraOf(classified: Classified): { extra?: BotProgram[] } {
  return classified.forExtra?.length ? { extra: classified.forExtra.slice(0, SHOWN_PROGRAMS) } : {};
}

export function reply(query: string, data: BotData): Reply {
  const queryTokens = tokenize(query);
  const classified = classifySearch(search(query, data.programs), parseQuery(query).stems);
  if (data.duration.triggers.some((trigger) => triggerMatches(trigger, queryTokens))) {
    const text = durationText(data.programs);
    if (text) {
      return { kind: "duration", text, anchor: data.duration.anchor, ...extraOf(classified) };
    }
  }
  const answer = findByTriggers(queryTokens, data.answers);
  if (answer) {
    return { kind: "answer", answer, ...extraOf(classified) };
  }
  const gap = findByTriggers(queryTokens, data.gaps);
  if (gap) {
    return { kind: "gap", gap };
  }
  if (classified.primary) {
    return { kind: "programs", intro: classified.primary.intro, programs: classified.primary.programs.slice(0, SHOWN_PROGRAMS) };
  }
  if (classified.weak?.length) {
    return { kind: "programs-weak", programs: classified.weak.slice(0, SHOWN_PROGRAMS) };
  }
  return { kind: "none", programs: upcoming(data.programs, NONE_PROGRAMS) };
}

export function detectIntent(query: string): Intent | null {
  const parsed = parseQuery(query);
  if (parsed.priceMax !== null || parsed.priceMin !== null || parsed.format || parsed.type) {
    return null;
  }
  const queryTokens = tokenize(query);
  const found = INTENT_TRIGGERS.find(([, triggers]) => triggers.some((trigger) => triggerMatches(trigger, queryTokens)));
  return found ? found[0] : null;
}
