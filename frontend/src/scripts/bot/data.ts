import type { BotData, BotProgram, Faq } from "./types";

const CATALOG_URL = "/api/catalog/bot";

let cached: Promise<BotData | null> | null = null;

async function fetchPrograms(): Promise<BotProgram[] | null> {
  const response = await fetch(CATALOG_URL, { credentials: "omit", headers: { Accept: "application/json" } });
  if (!response.ok) {
    return null;
  }
  const programs: unknown = await response.json();
  return Array.isArray(programs) ? (programs as BotProgram[]) : null;
}

async function loadFaq(): Promise<Faq> {
  const module = await import("../../data/bot-faq.json");
  return module.default as Faq;
}

async function loadAll(): Promise<BotData | null> {
  const [programs, faq] = await Promise.all([fetchPrograms(), loadFaq()]);
  return programs ? { programs, ...faq } : null;
}

export function loadBotData(): Promise<BotData | null> {
  cached ??= loadAll()
    .catch(() => null)
    .then((data) => {
      if (!data) {
        cached = null;
      }
      return data;
    });
  return cached;
}
