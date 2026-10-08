import { pluralRu } from "../lib/plural";
import { type Dropdown } from "./catalog-dropdowns";
import { closeButton, element, openDialog, type Dialog } from "./dialog";
import { attachSheet } from "./sheet-gesture";

export type Selection = Record<string, string[]>;

export interface SheetHandlers {
  applied: (group: string) => string[];
  preview: (selection: Selection) => number;
  apply: (selection: Selection) => void;
}

interface SheetParts {
  backdrop: HTMLElement;
  sheet: HTMLElement;
  title: HTMLElement;
  close: HTMLButtonElement;
  boxes: HTMLInputElement[];
  reset: HTMLButtonElement;
  apply: HTMLButtonElement;
}

function showLabel(count: number): string {
  return `Показать ${String(count)} ${pluralRu(count, "программу", "программы", "программ")}`;
}

function option(group: string, box: HTMLInputElement, checked: boolean): { label: HTMLLabelElement; input: HTMLInputElement } {
  const label = element("label", "fd-option");
  const input = element("input");
  input.type = "checkbox";
  input.name = `sheet-${group}`;
  input.value = box.value;
  input.dataset.value = box.value;
  input.checked = checked;
  const count = box.closest(".fd-option")?.querySelector(".fd-option-count")?.textContent ?? "";
  label.append(input, element("span", "fd-option-name", box.dataset.name ?? box.value), element("span", "fd-option-count", count));
  return { label, input };
}

function groupFieldset(dropdown: Dropdown, applied: string[]): { fieldset: HTMLFieldSetElement; inputs: HTMLInputElement[] } {
  const fieldset = element("fieldset", "filter-sheet-group");
  fieldset.dataset.group = dropdown.group;
  fieldset.appendChild(element("legend", "", dropdown.title));
  const inputs = dropdown.boxes.map((box) => {
    const { label, input } = option(dropdown.group, box, applied.includes(box.value));
    fieldset.appendChild(label);
    return input;
  });
  return { fieldset, inputs };
}

function build(dropdowns: Dropdown[], handlers: SheetHandlers): SheetParts {
  const backdrop = element("div", "filter-sheet-backdrop");
  const sheet = element("div", "filter-sheet");
  sheet.setAttribute("role", "dialog");
  sheet.setAttribute("aria-modal", "true");
  sheet.setAttribute("aria-labelledby", "filterSheetTitle");
  const title = element("h2", "", "Фильтры");
  title.id = "filterSheetTitle";
  title.tabIndex = -1;
  const close = closeButton("filter-sheet-close", "Закрыть фильтры");
  const body = element("div", "filter-sheet-body");
  const groups = dropdowns.map((dropdown) => groupFieldset(dropdown, handlers.applied(dropdown.group)));
  body.append(...groups.map((group) => group.fieldset));
  const reset = element("button", "fd-clear", "Сбросить");
  reset.type = "button";
  const apply = element("button", "fd-apply", "");
  apply.type = "button";
  const actions = element("div", "filter-sheet-actions");
  actions.append(reset, apply);
  sheet.append(close, title, body, actions);
  backdrop.appendChild(sheet);
  return { backdrop, sheet, title, close, boxes: groups.flatMap((group) => group.inputs), reset, apply };
}

function selectionOf(dropdowns: Dropdown[], boxes: HTMLInputElement[]): Selection {
  return Object.fromEntries(
    dropdowns.map((dropdown) => [
      dropdown.group,
      boxes.filter((box) => box.name === `sheet-${dropdown.group}` && box.checked).map((box) => box.value),
    ]),
  );
}

function open(dropdowns: Dropdown[], handlers: SheetHandlers, opener: Element | null): void {
  const parts = build(dropdowns, handlers);
  const update = (): void => {
    parts.apply.textContent = showLabel(handlers.preview(selectionOf(dropdowns, parts.boxes)));
  };
  update();
  const dialog: Dialog = openDialog({ backdrop: parts.backdrop, initialFocus: parts.title, opener });
  parts.sheet.addEventListener("change", update);
  parts.close.addEventListener("click", () => {
    dialog.close();
  });
  parts.reset.addEventListener("click", () => {
    parts.boxes.forEach((box) => {
      box.checked = false;
    });
    update();
  });
  parts.apply.addEventListener("click", () => {
    handlers.apply(selectionOf(dropdowns, parts.boxes));
    dialog.close();
  });
  attachSheet({ root: parts.backdrop, sheet: parts.sheet, grip: ".filter-sheet h2", onClose: () => dialog.close() });
}

export function showSheetTotal(count: number): void {
  document.querySelectorAll<HTMLElement>(".filter-sheet-open").forEach((button) => {
    const badge = button.querySelector<HTMLElement>("[data-sheet-count]");
    const number = button.querySelector<HTMLElement>("[data-sheet-count-value]");
    if (badge && number) {
      number.textContent = String(count);
      badge.hidden = count === 0;
    }
    button.classList.toggle("is-active", count > 0);
  });
}

export function setupFilterSheet(dropdowns: Dropdown[], handlers: SheetHandlers): void {
  document.querySelectorAll<HTMLElement>("[data-filter-sheet-open]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      open(dropdowns, handlers, button);
    });
  });
}
