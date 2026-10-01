import type { BotProgram } from "./types";

export type SearchProgram = Pick<BotProgram, "id" | "title"> & Partial<Omit<BotProgram, "id" | "title">>;
export type SearchReason = "empty" | "title" | "keywords" | "filter" | "none";

export interface ParsedQuery {
  stems: string[];
  priceMax: number | null;
  priceMin: number | null;
  format: string | null;
  type: string | null;
}

export interface SearchResult<T extends SearchProgram> {
  reason: SearchReason;
  programs: T[];
}

const ENDINGS = [
  "ниями", "ениям", "ования", "ование", "ением", "ения", "ение",
  "ями", "ами", "ого", "ому", "ыми", "ими", "ей", "ов", "ев",
  "ый", "ий", "ая", "яя", "ое", "ее", "ые", "ие", "ых", "их",
  "ой", "ом", "ам", "ах", "ям", "ях", "ы", "и", "а", "я", "о", "е", "у", "ю", "ь",
];
const MIN_STEM = 4;
const MIN_WORD = 3;
const MIN_PRICE_WITHOUT_UNIT = 1000;
const THOUSAND = 1000;
const PRICE_TAIL_CHARS = 12;
const NONE_LIMIT = 3;
const TITLE_WEIGHT = 3;
const KEYWORD_WEIGHT = 2;
const FORMATS: [RegExp, string][] = [
  [/онлайн|дистанц|удал/, "online"],
  [/очн|офлайн|аудитор/, "offline"],
  [/смешан/, "mixed"],
  [/гибрид/, "hybrid"],
];
const STOP_WORDS = ["программа", "курс", "обучение", "формат", "подобрать", "какой", "нужен", "документ", "старт", "стоит", "цена"];
const PRICE_RE = /(?<![а-яa-z])(до|дешевле|не дороже|не больше|за|от|дороже)\s+(\d[\d\s]*)\s*(тыс\w*|руб\w*|₽)?/;
const DURATION_TAIL_RE = /^\s*(месяц|недел|год|лет(?=$|[^а-яё])|час|дн)/;
const WORD_CHAR_RE = /[а-яa-z0-9]/;

export function normalize(word: string): string {
  return word.toLowerCase().replace(/ё/g, "е");
}

export function stem(word: string): string {
  const normalized = normalize(word);
  const ending = ENDINGS.find((end) => normalized.length - end.length >= MIN_STEM && normalized.endsWith(end));
  return ending ? normalized.slice(0, normalized.length - ending.length) : normalized;
}

export function sameStem(a: string, b: string): boolean {
  if (a === b) {
    return true;
  }
  const shorter = a.length < b.length ? a : b;
  if (shorter.length < MIN_STEM || Math.abs(a.length - b.length) < 2) {
    return false;
  }
  return a.startsWith(b) || b.startsWith(a);
}

const STOP_STEMS = STOP_WORDS.map(stem);

function charAt(text: string, index: number): string {
  return text.charAt(index);
}

function consumeWord(text: string, index: number, length: number): string {
  let start = index;
  let end = index + length;
  while (start > 0 && WORD_CHAR_RE.test(charAt(text, start - 1))) {
    start--;
  }
  while (end < text.length && WORD_CHAR_RE.test(charAt(text, end))) {
    end++;
  }
  return `${text.slice(0, start)} ${text.slice(end)}`;
}

function takePrice(text: string, out: ParsedQuery): string {
  const price = PRICE_RE.exec(text);
  if (!price) {
    return text;
  }
  const [whole, preposition = "", digits = "", unit] = price;
  let value = parseInt(digits.replace(/\s/g, ""), 10);
  const tail = text.slice(price.index + whole.length, price.index + whole.length + PRICE_TAIL_CHARS);
  if (DURATION_TAIL_RE.test(tail) || (!unit && value < MIN_PRICE_WITHOUT_UNIT)) {
    return text;
  }
  if (unit?.includes("тыс")) {
    value *= THOUSAND;
  }
  if (/^не\s/.test(preposition)) {
    out.priceMax = value;
  } else if (/от|дороже/.test(preposition)) {
    out.priceMin = value;
  } else {
    out.priceMax = value;
  }
  return consumeWord(text, price.index, whole.replace(/\s+$/, "").length);
}

function takeFormat(text: string, out: ParsedQuery): string {
  for (const [pattern, value] of FORMATS) {
    const found = pattern.exec(text);
    if (found) {
      out.format = value;
      return consumeWord(text, found.index, found[0].length);
    }
  }
  return text;
}

function takeType(text: string, out: ParsedQuery): string {
  const retraining = /переподготовк[а-яa-z]*|новая профессия/.exec(text);
  if (retraining) {
    out.type = "ПП";
    return consumeWord(text, retraining.index, retraining[0].length);
  }
  const qualification = /повышение квалификац[а-яa-z]*/.exec(text);
  if (qualification) {
    out.type = "ПК";
    return consumeWord(text, qualification.index, qualification[0].length);
  }
  const abbreviation = /(^|[^а-яa-z0-9])(пп|пк)(?=$|[^а-яa-z0-9])/.exec(text);
  if (abbreviation) {
    const [, before = "", code = ""] = abbreviation;
    out.type = code === "пп" ? "ПП" : "ПК";
    return consumeWord(text, abbreviation.index + before.length, code.length);
  }
  return text;
}

function stemsOf(text: string): string[] {
  return text
    .replace(/[^а-яa-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((word) => word.length >= MIN_WORD && !/^\d+$/.test(word))
    .map(stem)
    .filter((candidate) => !STOP_STEMS.some((stop) => sameStem(candidate, stop)));
}

export function parseQuery(query: string): ParsedQuery {
  const text = normalize(query);
  const out: ParsedQuery = { stems: [], priceMax: null, priceMin: null, format: null, type: null };
  if (!text.trim()) {
    return out;
  }
  const remaining = takeType(takeFormat(takePrice(text, out), out), out);
  out.stems = stemsOf(remaining);
  return out;
}

function hits(stems: string[], text: string): number {
  const words = normalize(text).replace(/[^а-яa-z0-9\s]/g, " ").split(/\s+/).map(stem);
  return stems.filter((candidate) => words.some((word) => sameStem(candidate, word))).length;
}

export function byStart(a: SearchProgram, b: SearchProgram): number {
  const aHas = Boolean(a.start_iso || a.start);
  const bHas = Boolean(b.start_iso || b.start);
  if (aHas !== bHas) {
    return aHas ? -1 : 1;
  }
  if (a.start_iso && b.start_iso) {
    return a.start_iso < b.start_iso ? -1 : a.start_iso > b.start_iso ? 1 : 0;
  }
  return 0;
}

function hasRestriction(query: ParsedQuery): boolean {
  return Boolean(query.format) || Boolean(query.type) || query.priceMax !== null || query.priceMin !== null;
}

function passes(query: ParsedQuery, program: SearchProgram): boolean {
  const price = program.price;
  if (query.format && program.format !== query.format) {
    return false;
  }
  if (query.type && program.type !== query.type) {
    return false;
  }
  if (query.priceMax !== null && !(typeof price === "number" && price <= query.priceMax)) {
    return false;
  }
  return !(query.priceMin !== null && !(typeof price === "number" && price >= query.priceMin));
}

interface Scored<T> {
  program: T;
  score: number;
  inTitle: number;
}

function score<T extends SearchProgram>(stems: string[], program: T): Scored<T> {
  const inTitle = hits(stems, program.title);
  const inWords = hits(stems, (program.keywords ?? []).join(" "));
  const inSphere = hits(stems, program.sphere ?? "");
  return { program, score: inTitle * TITLE_WEIGHT + inWords * KEYWORD_WEIGHT + inSphere, inTitle };
}

function byRelevance<T>(a: Scored<T>, b: Scored<T>): number {
  const aTier = a.inTitle > 0 ? 1 : 0;
  const bTier = b.inTitle > 0 ? 1 : 0;
  return aTier !== bTier ? bTier - aTier : b.score - a.score;
}

export function search<T extends SearchProgram>(query: string, programs: T[]): SearchResult<T> {
  const parsed = parseQuery(query);
  if (!parsed.stems.length && !hasRestriction(parsed)) {
    return { reason: "empty", programs: [] };
  }
  const filtered = programs.filter((program) => passes(parsed, program));
  const scored = filtered
    .map((program) => score(parsed.stems, program))
    .filter((row) => row.score > 0)
    .sort(byRelevance);
  const best = scored[0];
  if (best) {
    return { reason: best.inTitle > 0 ? "title" : "keywords", programs: scored.map((row) => row.program) };
  }
  if (hasRestriction(parsed) && filtered.length) {
    return { reason: "filter", programs: filtered };
  }
  return { reason: "none", programs: [...programs].sort(byStart).slice(0, NONE_LIMIT) };
}
