import { element } from "../dialog";
import { OTHER_PROGRAMS, PROGRAMS_ENDPOINT } from "./constants";

export interface ProgramOption {
  id: string;
  title: string;
  url: string;
  sphere: string;
}

let cached: Promise<ProgramOption[]> | null = null;

export function loadPrograms(): Promise<ProgramOption[]> {
  cached ??= fetch(PROGRAMS_ENDPOINT, { credentials: "omit" })
    .then((response) => (response.ok ? (response.json() as Promise<ProgramOption[]>) : []))
    .catch(() => []);
  return cached;
}

function grouped(items: ProgramOption[]): Map<string, ProgramOption[]> {
  const groups = new Map<string, ProgramOption[]>();
  items.forEach((item) => {
    const key = item.sphere || OTHER_PROGRAMS;
    groups.set(key, [...(groups.get(key) ?? []), item]);
  });
  return groups;
}

export function programOption(id: string, title: string, url: string): HTMLOptionElement {
  const option = element("option", "", title);
  option.value = id;
  option.dataset.url = url;
  return option;
}

export function fillPrograms(select: HTMLSelectElement, items: ProgramOption[]): void {
  if (!items.length || select.dataset.filled) {
    return;
  }
  grouped(items).forEach((options, sphere) => {
    const group = element("optgroup");
    group.label = sphere;
    group.append(...options.map((item) => programOption(item.id, item.title, item.url)));
    select.appendChild(group);
  });
  select.dataset.filled = "1";
}
