export const CATALOG_LINK_LABEL = "Портфель программ";
export const CATALOG_PATH = "/catalog";
export const ANNOUNCEMENTS_LINK_LABEL = "Анонсы программ";
export const ANNOUNCEMENTS_PATH = "/announcements";
export const RATINGS_PATH = "/ratings";
export const LANDING_PATH = "/";
export const APPLY_SECTION = "contacts";

interface PageItem {
  label: string;
  path: string;
}

interface SectionItem {
  label: string;
  section: string;
}

export type NavItem = PageItem | SectionItem;

export const MAIN_NAV: readonly NavItem[] = [
  { label: CATALOG_LINK_LABEL, path: CATALOG_PATH },
  { label: ANNOUNCEMENTS_LINK_LABEL, path: ANNOUNCEMENTS_PATH },
  { label: "Форматы", section: "formats" },
  { label: "Преподаватели", section: "teachers" },
  { label: "Рейтинги", path: RATINGS_PATH },
  { label: "Контакты", section: APPLY_SECTION },
];

export function sectionHref(section: string, current: string): string {
  return current === LANDING_PATH ? `#${section}` : `${LANDING_PATH}#${section}`;
}

export function navHref(item: NavItem, current: string): string {
  return "path" in item ? item.path : sectionHref(item.section, current);
}

export function isCurrent(item: NavItem, current: string): boolean {
  return "path" in item && item.path === current;
}
