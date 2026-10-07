import { fetchOptional } from "./api";

export interface Thumb {
  src: string;
  webp: string;
  alt: string;
}

export interface Tag {
  kind: string;
  text: string;
  tip: string;
}

export interface Compare {
  format: string;
  duration: string;
  start: string;
  modules: string;
  teachers: string;
  audience: string;
}

export interface Card {
  hse_id: string;
  title: string;
  path: string;
  type_short: string;
  format: string;
  sphere: string;
  sphere_title: string;
  duration: string;
  price_sort: number;
  start_sort: number;
  title_sort: string;
  search: string;
  thumb: Thumb | null;
  tags: Tag[];
  start: string;
  price: string;
  compare: Compare;
  high_rating: boolean;
}

export interface Chip {
  label: string;
  value: string;
  active: boolean;
}

export interface Filters {
  type: Chip[];
  format: Chip[];
  sphere: Chip[];
  duration: Chip[];
}

export interface LegendEntry {
  slug: string;
  title: string;
}

export interface Start {
  side: "left" | "right";
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

export interface CatalogPage {
  total: number;
  total_label: string;
  canonical_url: string;
  image_url: string;
  filters: Filters;
  cards: Card[];
  starts: Starts | null;
  structured_data: string;
}

export function fetchCatalogPage(): Promise<CatalogPage | null> {
  return fetchOptional<CatalogPage>("/catalog/programs");
}
