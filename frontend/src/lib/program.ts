export interface Cover {
  src: string;
  srcset: string;
  webp_srcset: string;
  width: number;
  height: number;
  alt: string;
}

export interface About {
  lead: string;
  body: string;
  items: string[];
}

export interface Audience {
  intro: string;
  items: string[];
}

export interface Module {
  title: string;
  hours: string;
  topics: string[];
}

export interface ProgramFile {
  label: string;
  size: string;
  url: string;
}

export interface Teacher {
  name: string;
  about: string;
  page_url: string;
}

export interface Review {
  text: string;
  author: string;
}

export interface Faq {
  question: string;
  answer: string;
}

export interface Notice {
  date: string;
  text: string;
  url: string;
  host: string;
}

export interface Fact {
  label: string;
  value: string;
}

export interface Credential {
  tag: string;
  name: string;
  note: string;
}

export interface Sibling {
  title: string;
  path: string;
}

export interface Siblings {
  sphere_title: string;
  count_label: string;
  items: Sibling[];
}

export interface ProgramPage {
  hse_id: string;
  title: string;
  path: string;
  canonical_url: string;
  page_title: string;
  description: string;
  image_url: string;
  structured_data: string[];
  crumb: string;
  chips: string[];
  cover: Cover | null;
  notice: Notice | null;
  about: About | null;
  audience: Audience | null;
  results: string[];
  advantages: string[];
  modules: Module[];
  modules_label: string;
  files: ProgramFile[];
  teachers_heading: string;
  teachers: Teacher[];
  reviews: Review[];
  admission_documents: string[];
  faq: Faq[];
  siblings: Siblings | null;
  price: string;
  price_terms: string[];
  facts: Fact[];
  pay_url: string;
  hse_url: string;
  credential: Credential | null;
}

const PAGE_PATTERN = /(?:^|-)(\d+)(?:\.html)?$/;

export function programIdFromPage(page: string): string | null {
  return PAGE_PATTERN.exec(page)?.[1] ?? null;
}

export function sitePath(path: string): string {
  return `/${path}`;
}
