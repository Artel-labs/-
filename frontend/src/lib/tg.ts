import { ApiError, fetchOptional } from "./api";

export interface TgModule {
  title: string;
  hours: string;
  topics: string[];
}

export interface TgNotice {
  date: string | null;
  text: string;
  url: string | null;
}

export interface TgFile {
  title: string;
  size: string;
  path: string;
}

export interface TgTeacher {
  name: string;
  about: string;
  photo: string | null;
  page: string | null;
}

export interface TgProgram {
  id: string;
  title: string;
  sphere: string | null;
  badge: string | null;
  doc: string | null;
  format: string | null;
  duration: string | null;
  hours: string | null;
  start_label: string | null;
  price: number | null;
  old_price: number | null;
  tagline: string;
  audience: string[];
  results: string[];
  modules: TgModule[];
  cover: string | null;
  thumb: string | null;
  pay: string | null;
  about: string;
  lead: string | null;
  about_items: string[] | null;
  audience_intro: string | null;
  advantages: string[];
  language: string | null;
  schedule: string | null;
  price_terms: string[];
  notice: TgNotice | null;
  files: TgFile[];
  teachers: TgTeacher[];
  feedback: { text: string; author: string }[];
  admission_docs: string[];
  faq: { q: string; a: string }[];
}

export interface TgSphere {
  id: string;
  title: string;
  count: number;
}

export interface TgCatalog {
  programs: TgProgram[];
  spheres: TgSphere[];
}

const TG_PATH = "/catalog/tg";
const NOT_FOUND = 404;

export async function fetchTgCatalog(): Promise<TgCatalog> {
  const catalog = await fetchOptional<TgCatalog>(TG_PATH);
  if (!catalog) {
    throw new ApiError(TG_PATH, NOT_FOUND);
  }
  return catalog;
}

export function embeddedJson(value: unknown): string {
  return JSON.stringify(value).replace(/</g, "\\u003C");
}
