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
  teachers: number;
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

export interface Month {
  label: string;
  count: number;
  left: number;
  width: number;
  scroll: number;
}

export interface Tick {
  left: number;
  kind: string;
}

export interface Start {
  lane: string;
  left: number;
  pin: number;
  path: string;
  hint: string;
  when: string;
  title: string;
  sphere: string;
  meta: string;
  price: string;
}

export interface Starts {
  width: number;
  months: Month[];
  ticks: Tick[];
  today: number | null;
  items: Start[];
}

export interface CatalogPage {
  total: number;
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
