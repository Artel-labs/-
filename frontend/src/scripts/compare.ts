const MAX_SELECTED = 3;
const MIN_TO_COMPARE = 2;
const PARAM = "compare";
const LIST_SEPARATOR = " · ";
const CLOSE_DELAY_MS = 240;
const ID_PATTERN = /^[\w-]{1,40}$/;
const TYPE_FULL: Record<string, string> = { ПК: "Повышение квалификации", ПП: "Профессиональная переподготовка" };

interface Row {
  label: string;
  value: (card: HTMLElement) => string;
  list?: boolean;
}

function attribute(name: string): (card: HTMLElement) => string {
  return (card) => (card.getAttribute(name) ?? "").trim();
}

const ROWS: Row[] = [
  {
    label: "Документ",
    value: (card) => {
      const type = attribute("data-type")(card);
      return TYPE_FULL[type] ?? type;
    },
  },
  { label: "Формат", value: attribute("data-cmp-format") },
  { label: "Длительность", value: attribute("data-cmp-duration") },
  { label: "Старт", value: (card) => attribute("data-cmp-start")(card).replace(/^Старт:\s*/, "").trim() },
  { label: "Цена", value: (card) => card.querySelector(".price")?.textContent.trim() ?? "" },
  {
    label: "Модулей",
    value: (card) => {
      const modules = attribute("data-cmp-modules")(card);
      return modules ? String(modules.split(LIST_SEPARATOR).filter(Boolean).length) : "";
    },
  },
  { label: "Модули", value: attribute("data-cmp-modules"), list: true },
  { label: "Преподавателей", value: attribute("data-cmp-teachers") },
  { label: "Для кого", value: attribute("data-cmp-audience"), list: true },
];

let selected: string[] = [];
let bar: HTMLElement | null = null;
let backdrop: HTMLElement | null = null;
let lastTrigger: Element | null = null;
let hidden: [Element, string | null][] = [];

function element<K extends keyof HTMLElementTagNameMap>(tag: K, className = "", text = ""): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) {
    node.className = className;
  }
  if (text) {
    node.textContent = text;
  }
  return node;
}

function cardById(id: string): HTMLElement | null {
  return ID_PATTERN.test(id) ? document.querySelector<HTMLElement>(`.card[data-id="${id}"]`) : null;
}

function titleOf(card: HTMLElement): string {
  return card.querySelector("h3")?.textContent.trim() ?? "";
}

function hrefOf(card: HTMLElement): string {
  return card.querySelector(".card-link")?.getAttribute("href") ?? "";
}

function readUrl(): string[] {
  const raw = new URLSearchParams(window.location.search).get(PARAM);
  return raw ? raw.split(",").slice(0, MAX_SELECTED).filter((id) => cardById(id)) : [];
}

function writeUrl(): void {
  const params = new URLSearchParams(window.location.search);
  if (selected.length) {
    params.set(PARAM, selected.join(","));
  } else {
    params.delete(PARAM);
  }
  const query = params.toString().replace(/%2C/g, ",");
  history.replaceState(null, "", window.location.pathname + (query ? `?${query}` : "") + window.location.hash);
}

function syncToggles(): void {
  document.querySelectorAll("[data-compare-toggle]").forEach((toggleButton) => {
    const id = toggleButton.closest(".card")?.getAttribute("data-id") ?? "";
    toggleButton.setAttribute("aria-pressed", String(selected.includes(id)));
  });
}

function say(text: string): void {
  const hint = bar?.querySelector(".cmp-bar-hint");
  if (hint) {
    hint.textContent = text;
  }
}

function changed(): void {
  syncToggles();
  writeUrl();
  renderBar();
}

function toggle(id: string): void {
  if (selected.includes(id)) {
    selected = selected.filter((item) => item !== id);
  } else if (selected.length >= MAX_SELECTED) {
    say("Можно сравнить не больше трёх программ – снимите одну.");
    return;
  } else {
    selected = [...selected, id];
  }
  changed();
}

function clearAll(): void {
  selected = [];
  changed();
}

function buildBar(): HTMLElement {
  const node = element("div", "cmp-bar");
  node.setAttribute("role", "region");
  node.setAttribute("aria-label", "Сравнение программ");
  const count = element("span", "cmp-bar-count");
  count.setAttribute("aria-live", "polite");
  const actions = element("span", "cmp-bar-actions");
  const clear = element("button", "cmp-clear", "Очистить");
  const openButton = element("button", "cmp-open", "Сравнить");
  clear.type = "button";
  openButton.type = "button";
  clear.addEventListener("click", clearAll);
  openButton.addEventListener("click", () => {
    open(openButton);
  });
  actions.append(clear, openButton);
  node.append(count, element("span", "cmp-bar-hint"), element("ul", "cmp-bar-list"), actions);
  document.body.appendChild(node);
  return node;
}

function barChip(id: string, card: HTMLElement): HTMLLIElement {
  const item = element("li");
  const chip = element("button", "cmp-chip");
  chip.type = "button";
  chip.setAttribute("aria-label", `Убрать из сравнения: ${titleOf(card)}`);
  chip.appendChild(element("span", "", titleOf(card)));
  chip.addEventListener("click", () => {
    toggle(id);
  });
  item.appendChild(chip);
  return item;
}

function renderBar(): void {
  bar ??= buildBar();
  const isOpen = selected.length > 0;
  bar.classList.toggle("is-open", isOpen);
  document.documentElement.classList.toggle("has-cmp-bar", isOpen);
  if (!isOpen) {
    return;
  }
  const count = bar.querySelector(".cmp-bar-count");
  const openButton = bar.querySelector<HTMLButtonElement>(".cmp-open");
  const list = bar.querySelector(".cmp-bar-list");
  if (count) {
    count.textContent = `Выбрано ${String(selected.length)} из ${String(MAX_SELECTED)}`;
  }
  say(selected.length < MIN_TO_COMPARE ? "Отметьте ещё одну программу" : "");
  if (openButton) {
    openButton.disabled = selected.length < MIN_TO_COMPARE;
  }
  list?.replaceChildren(
    ...selected.flatMap((id) => {
      const card = cardById(id);
      return card ? [barChip(id, card)] : [];
    }),
  );
}

function valueCell(row: Row, value: string): HTMLTableCellElement {
  const cell = element("td");
  if (!value) {
    cell.className = "cmp-none";
    cell.textContent = "—";
    return cell;
  }
  if (!row.list) {
    cell.textContent = value;
    return cell;
  }
  const list = element("ul", "cmp-list");
  value.split(LIST_SEPARATOR).forEach((item) => {
    const text = item.replace(/[,;]+$/, "").trim();
    if (text) {
      list.appendChild(element("li", "", text));
    }
  });
  cell.appendChild(list);
  return cell;
}

function tableRow(row: Row, cards: HTMLElement[]): HTMLTableRowElement | null {
  const values = cards.map((card) => row.value(card));
  if (!values.some(Boolean)) {
    return null;
  }
  const line = element("tr", new Set(values).size > 1 ? "is-diff" : "");
  const heading = element("th", "", row.label);
  heading.scope = "row";
  line.append(heading, ...values.map((value) => valueCell(row, value)));
  return line;
}

function headRow(cards: HTMLElement[]): HTMLTableSectionElement {
  const head = element("thead");
  const line = element("tr");
  line.appendChild(element("th"));
  cards.forEach((card) => {
    const heading = element("th");
    heading.scope = "col";
    const link = element("a", "", titleOf(card));
    link.href = hrefOf(card);
    heading.appendChild(link);
    line.appendChild(heading);
  });
  head.appendChild(line);
  return head;
}

function applyButton(card: HTMLElement): HTMLButtonElement {
  const button = element("button", "cmp-apply", "Подать заявку");
  button.type = "button";
  button.setAttribute("data-application", "");
  button.setAttribute("data-program-id", card.getAttribute("data-id") ?? "");
  button.setAttribute("data-program-title", titleOf(card));
  button.setAttribute("data-program-url", hrefOf(card));
  button.setAttribute("aria-label", `Заявка: ${titleOf(card)}`);
  button.addEventListener("click", () => {
    shut(true);
  });
  return button;
}

function actionsRow(cards: HTMLElement[]): HTMLTableRowElement {
  const line = element("tr", "cmp-actions");
  line.appendChild(element("td"));
  cards.forEach((card) => {
    const cell = element("td");
    cell.appendChild(applyButton(card));
    line.appendChild(cell);
  });
  return line;
}

function buildTable(cards: HTMLElement[]): HTMLTableElement {
  const table = element("table", "cmp-table");
  const body = element("tbody");
  ROWS.forEach((row) => {
    const line = tableRow(row, cards);
    if (line) {
      body.appendChild(line);
    }
  });
  body.appendChild(actionsRow(cards));
  table.append(headRow(cards), body);
  return table;
}

function buildWindow(cards: HTMLElement[]): { node: HTMLElement; heading: HTMLElement } {
  const node = element("div", "cmp-window");
  node.setAttribute("role", "dialog");
  node.setAttribute("aria-modal", "true");
  node.setAttribute("aria-labelledby", "cmp-title");
  const heading = element("h2", "", "Сравнение программ");
  heading.id = "cmp-title";
  heading.tabIndex = -1;
  const close = element("button", "cmp-close", "×");
  close.type = "button";
  close.setAttribute("aria-label", "Закрыть сравнение");
  close.addEventListener("click", () => {
    shut(false);
  });
  const scroll = element("div", "cmp-scroll");
  scroll.appendChild(buildTable(cards));
  node.append(close, heading, element("p", "cmp-sub", "Точкой отмечены строки, в которых программы различаются."), scroll);
  return { node, heading };
}

function makeInert(except: Element): void {
  hidden = [...document.body.children]
    .filter((node) => node !== except)
    .map((node) => {
      const pair: [Element, string | null] = [node, node.getAttribute("aria-hidden")];
      node.setAttribute("aria-hidden", "true");
      if (node instanceof HTMLElement) {
        node.inert = true;
      }
      return pair;
    });
}

function restoreInert(): void {
  hidden.forEach(([node, value]) => {
    if (value === null) {
      node.removeAttribute("aria-hidden");
    } else {
      node.setAttribute("aria-hidden", value);
    }
    if (node instanceof HTMLElement) {
      node.inert = false;
    }
  });
  hidden = [];
}

function focusables(container: HTMLElement): HTMLElement[] {
  return [...container.querySelectorAll<HTMLElement>("a[href], button:not([disabled])")].filter(
    (node) => node.offsetParent !== null || node === document.activeElement,
  );
}

function trapTab(event: KeyboardEvent, container: HTMLElement): void {
  const items = focusables(container);
  const first = items[0];
  const last = items.at(-1);
  if (!first || !last) {
    return;
  }
  const active = document.activeElement;
  if (event.shiftKey && (active === first || !container.contains(active))) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && active === last) {
    event.preventDefault();
    first.focus();
  }
}

function onKey(event: KeyboardEvent): void {
  if (!backdrop) {
    return;
  }
  if (event.key === "Escape") {
    event.preventDefault();
    shut(false);
  } else if (event.key === "Tab") {
    trapTab(event, backdrop);
  }
}

function open(trigger: Element): void {
  const cards = selected.map(cardById).filter((card): card is HTMLElement => card !== null);
  if (cards.length < MIN_TO_COMPARE) {
    return;
  }
  lastTrigger = trigger;
  const node = element("div", "cmp-backdrop");
  const { node: windowNode, heading } = buildWindow(cards);
  node.appendChild(windowNode);
  document.body.appendChild(node);
  backdrop = node;
  makeInert(node);
  document.documentElement.style.overflow = "hidden";
  node.addEventListener("mousedown", (event) => {
    if (event.target === node) {
      shut(false);
    }
  });
  document.addEventListener("keydown", onKey, true);
  requestAnimationFrame(() => {
    node.classList.add("is-open");
    heading.focus();
  });
}

function shut(keepFocus: boolean): void {
  const node = backdrop;
  if (!node) {
    return;
  }
  backdrop = null;
  document.removeEventListener("keydown", onKey, true);
  restoreInert();
  document.documentElement.style.overflow = "";
  node.classList.remove("is-open");
  if (keepFocus) {
    node.remove();
    return;
  }
  window.setTimeout(() => {
    node.remove();
  }, CLOSE_DELAY_MS);
  if (lastTrigger instanceof HTMLElement && document.contains(lastTrigger)) {
    lastTrigger.focus();
  }
}

export function setupCompare(): void {
  if (!document.querySelector("[data-compare-toggle]")) {
    return;
  }
  selected = readUrl();
  syncToggles();
  if (selected.length) {
    renderBar();
  }
  document.addEventListener("click", (event) => {
    const toggleButton = event.target instanceof Element ? event.target.closest("[data-compare-toggle]") : null;
    const id = toggleButton?.closest(".card")?.getAttribute("data-id");
    if (id) {
      event.preventDefault();
      toggle(id);
    }
  });
}
