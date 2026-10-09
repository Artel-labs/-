import { fetchOptional } from "./api";
import type { LegendEntry } from "./catalog";

export interface Start {
  path: string;
  hint: string;
  when: string;
  title: string;
  sphere: string;
  meta: string;
  price: string;
}

export interface StartMonth {
  anchor: string;
  label: string;
  caption: string;
  items: Start[];
}

export interface Starts {
  months: StartMonth[];
  legend: LegendEntry[];
}

export interface AnnouncementsPage {
  canonical_url: string;
  starts: Starts | null;
}

export function fetchAnnouncementsPage(): Promise<AnnouncementsPage | null> {
  return fetchOptional<AnnouncementsPage>("/catalog/announcements");
}
