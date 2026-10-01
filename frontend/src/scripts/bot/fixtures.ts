import { readFileSync } from "node:fs";

import type { BotData, BotProgram, Faq } from "./types";

interface LegacyProgram extends Omit<BotProgram, "format_label" | "price_label" | "start_iso"> {
  formatLabel: string;
  priceLabel: string;
  startIso: string | null;
}

const LEGACY_CATALOG = new URL("../../../../backend/tests/fixtures/legacy_bot_catalog.json", import.meta.url);
const FAQ = new URL("../../data/bot-faq.json", import.meta.url);

function fromLegacy({ formatLabel, priceLabel, startIso, ...rest }: LegacyProgram): BotProgram {
  return { ...rest, url: `/${rest.url}`, format_label: formatLabel, price_label: priceLabel, start_iso: startIso };
}

export function catalogPrograms(): BotProgram[] {
  const legacy = JSON.parse(readFileSync(LEGACY_CATALOG, "utf8")) as { programs: LegacyProgram[] };
  return legacy.programs.map(fromLegacy);
}

export function faq(): Faq {
  return JSON.parse(readFileSync(FAQ, "utf8")) as Faq;
}

export function botData(): BotData {
  return { programs: catalogPrograms(), ...faq() };
}
