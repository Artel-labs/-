import { matchPrograms, type ProgramChoice } from "../../lib/hse-forms";
import { element } from "../dialog";
import { NOTHING_FOUND, OTHER_PROGRAMS, SEARCH_LABEL, SEARCH_PLACEHOLDER } from "./constants";

const SEARCH_ID = "dpo-app-search";

function grouped(items: readonly ProgramChoice[]): Map<string, ProgramChoice[]> {
  const groups = new Map<string, ProgramChoice[]>();
  items.forEach((item) => {
    const key = item.sphere || OTHER_PROGRAMS;
    groups.set(key, [...(groups.get(key) ?? []), item]);
  });
  return groups;
}

function programButton(program: ProgramChoice, onPick: (program: ProgramChoice) => void): HTMLLIElement {
  const item = element("li");
  const button = element("button", "dpo-app-choice", program.title);
  button.type = "button";
  button.addEventListener("click", () => {
    onPick(program);
  });
  item.appendChild(button);
  return item;
}

function renderList(list: HTMLElement, items: readonly ProgramChoice[], onPick: (program: ProgramChoice) => void): void {
  if (!items.length) {
    list.replaceChildren(element("p", "dpo-app-empty", NOTHING_FOUND));
    return;
  }
  list.replaceChildren(
    ...[...grouped(items)].map(([sphere, programs]) => {
      const group = element("section", "dpo-app-group");
      const choices = element("ul", "dpo-app-choices");
      choices.append(...programs.map((program) => programButton(program, onPick)));
      group.append(element("h3", "dpo-app-sphere", sphere), choices);
      return group;
    }),
  );
}

export function buildChooser(programs: readonly ProgramChoice[], onPick: (program: ProgramChoice) => void): HTMLElement {
  const root = element("div", "dpo-app-chooser");
  const label = element("label", "dpo-app-search-label", SEARCH_LABEL);
  const search = element("input", "dpo-app-search");
  const list = element("div", "dpo-app-list");
  label.htmlFor = SEARCH_ID;
  search.id = SEARCH_ID;
  search.type = "search";
  search.placeholder = SEARCH_PLACEHOLDER;
  search.autocomplete = "off";
  search.addEventListener("input", () => {
    renderList(list, matchPrograms(programs, search.value), onPick);
  });
  renderList(list, programs, onPick);
  root.append(label, search, list);
  return root;
}
