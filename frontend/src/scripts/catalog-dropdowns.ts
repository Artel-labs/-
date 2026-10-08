const ACTIVE_CLASS = "is-active";
const END_CLASS = "is-end";
const EDGE_GAP_PX = 8;

export interface Dropdown {
  group: string;
  title: string;
  root: HTMLElement;
  toggle: HTMLButtonElement;
  panel: HTMLElement;
  boxes: HTMLInputElement[];
}

export interface DropdownHandlers {
  applied: (group: string) => string[];
  apply: (group: string, values: string[]) => void;
}

function dropdownOf(root: HTMLElement): Dropdown | null {
  const toggle = root.querySelector("[data-filter-toggle]");
  const panel = root.querySelector<HTMLElement>("[data-filter-panel]");
  const group = root.dataset.group;
  if (!(toggle instanceof HTMLButtonElement) || !panel || !group) {
    return null;
  }
  const boxes = [...panel.querySelectorAll<HTMLInputElement>("input[type=checkbox]")];
  return { group, title: root.dataset.title ?? group, root, toggle, panel, boxes };
}

export function findDropdowns(): Dropdown[] {
  return [...document.querySelectorAll<HTMLElement>("[data-filter]")]
    .map(dropdownOf)
    .filter((dropdown): dropdown is Dropdown => dropdown !== null);
}

export function valuesOf(dropdown: Dropdown): string[] {
  return dropdown.boxes.map((box) => box.value);
}

export function nameOf(dropdown: Dropdown, value: string): string {
  return dropdown.boxes.find((box) => box.value === value)?.dataset.name ?? value;
}

function checkedValues(dropdown: Dropdown): string[] {
  return dropdown.boxes.filter((box) => box.checked).map((box) => box.value);
}

function showCount(dropdown: Dropdown, count: number): void {
  const badge = dropdown.toggle.querySelector<HTMLElement>("[data-filter-count]");
  const number = dropdown.toggle.querySelector<HTMLElement>("[data-filter-count-value]");
  if (badge && number) {
    number.textContent = String(count);
    badge.hidden = count === 0;
  }
  dropdown.toggle.classList.toggle(ACTIVE_CLASS, count > 0);
}

export function showSelection(dropdown: Dropdown, values: readonly string[]): void {
  dropdown.boxes.forEach((box) => {
    box.checked = values.includes(box.value);
  });
  showCount(dropdown, values.length);
}

function isOpen(dropdown: Dropdown): boolean {
  return !dropdown.panel.hidden;
}

function keepInViewport(dropdown: Dropdown): void {
  dropdown.panel.classList.remove(END_CLASS);
  const overflows = dropdown.panel.getBoundingClientRect().right > window.innerWidth - EDGE_GAP_PX;
  dropdown.panel.classList.toggle(END_CLASS, overflows);
}

function open(dropdown: Dropdown): void {
  dropdown.panel.hidden = false;
  dropdown.toggle.setAttribute("aria-expanded", "true");
  keepInViewport(dropdown);
}

function close(dropdown: Dropdown, handlers: DropdownHandlers): void {
  dropdown.panel.hidden = true;
  dropdown.toggle.setAttribute("aria-expanded", "false");
  showSelection(dropdown, handlers.applied(dropdown.group));
}

function closeOthers(dropdowns: Dropdown[], current: Dropdown | null, handlers: DropdownHandlers): void {
  dropdowns
    .filter((dropdown) => dropdown !== current && isOpen(dropdown))
    .forEach((dropdown) => {
      close(dropdown, handlers);
    });
}

function bindDropdown(dropdowns: Dropdown[], dropdown: Dropdown, handlers: DropdownHandlers): void {
  dropdown.toggle.addEventListener("click", () => {
    closeOthers(dropdowns, dropdown, handlers);
    if (isOpen(dropdown)) {
      close(dropdown, handlers);
    } else {
      open(dropdown);
    }
  });
  dropdown.panel.querySelector("[data-filter-clear]")?.addEventListener("click", () => {
    dropdown.boxes.forEach((box) => {
      box.checked = false;
    });
  });
  dropdown.panel.querySelector("[data-filter-apply]")?.addEventListener("click", () => {
    handlers.apply(dropdown.group, checkedValues(dropdown));
    close(dropdown, handlers);
    dropdown.toggle.focus();
  });
}

function bindDismiss(dropdowns: Dropdown[], handlers: DropdownHandlers): void {
  document.addEventListener("pointerdown", (event) => {
    const target = event.target;
    const inside = target instanceof Node && dropdowns.some((dropdown) => dropdown.root.contains(target));
    if (!inside) {
      closeOthers(dropdowns, null, handlers);
    }
  });
  document.addEventListener("keydown", (event) => {
    const opened = dropdowns.find(isOpen);
    if (event.key === "Escape" && opened) {
      close(opened, handlers);
      opened.toggle.focus();
    }
  });
}

export function setupDropdowns(dropdowns: Dropdown[], handlers: DropdownHandlers): void {
  dropdowns.forEach((dropdown) => {
    bindDropdown(dropdowns, dropdown, handlers);
  });
  bindDismiss(dropdowns, handlers);
}
