import { fetchOptional } from "./api";

export interface Link {
  href: string;
  title: string;
}

export interface SphereCard {
  slug: string;
  href: string;
  index: string;
  title: string;
  lead: string;
  facts: string[];
}

export interface FormatDoc {
  file: string;
  ext: string;
  height: number;
  name: string;
}

export interface FormatStat {
  key: string;
  value: string;
}

export interface FormatCta {
  href: string;
  label: string;
  external: boolean;
  application: boolean;
}

export interface Format {
  step: number;
  index: string;
  title: string;
  desc: string;
  document: string;
  doc: FormatDoc | null;
  stats: FormatStat[];
  start: string;
  count: string;
  cta: FormatCta;
}

export interface TeacherPhoto {
  src: string;
  webp: string;
  alt: string;
}

export interface TeacherCard {
  payload: string;
  initials: string;
  photo: TeacherPhoto | null;
  name: string;
  page: string;
  more_label: string;
  count: string;
  about: string;
}

export interface StartStrip {
  path: string;
  label: string;
  big: string;
  small: string;
  is_month: boolean;
  title: string;
}

export interface ReviewCard {
  text: string;
  author: string;
  path: string;
  program: string;
}

export interface TopProgram {
  image: string;
  image_webp: string;
  id: string;
  start: string;
  title: string;
  kind: string;
  format: string;
  format_tip: string;
  doc: string;
  doc_tip: string;
  duration: string;
  path: string;
}

export interface NoscriptGroup {
  title: string;
  lead: string;
  links: Link[];
}

export interface Landing {
  canonical_url: string;
  branches: string[];
  image_url: string;
  spheres: SphereCard[];
  formats: Format[];
  teachers: TeacherCard[];
  starts: StartStrip[];
  reviews: ReviewCard[];
  top: TopProgram[];
  noscript: NoscriptGroup[];
}

export function fetchLanding(): Promise<Landing | null> {
  return fetchOptional<Landing>("/catalog/landing");
}
