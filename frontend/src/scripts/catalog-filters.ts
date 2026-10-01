const GROUPS = ["type", "format", "sphere", "duration"] as const;
const ALL = "all";
const DEFAULT_SORT = "default";
const SEARCH_DELAY_MS = 160;
const LEAVE_MS = 280;
const ENTER_STAGGER_MS = 35;
const CARD_SELECTOR = ".card[data-type]";

type Group = (typeof GROUPS)[number];

interface Elements {
  grid: HTMLElement;
  empty: HTMLElement;
  search: HTMLInputElement;
  reset: HTMLButtonElement;
  count: HTMLElement;
  sort: HTMLSelectElement;
}

interface State {
  active: Record<Group, string>;
  sortBy: string;
  query: string;
}

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const leaveMs = reduceMotion ? 0 : LEAVE_MS;
const enterStaggerMs = reduceMotion ? 0 : ENTER_STAGGER_MS;

function isGroup(value: string | undefined): value is Group {
  return GROUPS.some((group) => group === value);
}

function cardsOf(elements: Elements): HTMLElement[] {
  return [...elements.grid.querySelectorAll<HTMLElement>(CARD_SELECTOR)];
}

function matches(state: State, card: HTMLElement): boolean {
  const passes = GROUPS.every((group) => state.active[group] === ALL || card.dataset[group] === state.active[group]);
  const query = state.query.trim().toLowerCase();
  return passes && (!query || (card.dataset.search ?? "").toLowerCase().includes(query));
}

function isDirty(state: State): boolean {
  return GROUPS.some((group) => state.active[group] !== ALL) || state.query.trim() !== "" || state.sortBy !== DEFAULT_SORT;
}

function numberOf(card: HTMLElement, key: string): number {
  return Number(card.dataset[key]) || 0;
}

function startOf(card: HTMLElement): number {
  return numberOf(card, "start") || Infinity;
}

const COMPARATORS: Record<string, (a: HTMLElement, b: HTMLElement) => number> = {
  "price-asc": (a, b) => numberOf(a, "price") - numberOf(b, "price"),
  "price-desc": (a, b) => numberOf(b, "price") - numberOf(a, "price"),
  start: (a, b) => startOf(a) - startOf(b),
  title: (a, b) => (a.dataset.title ?? "").localeCompare(b.dataset.title ?? "", "ru"),
};

function applySort(state: State, cards: HTMLElement[]): void {
  const comparator = COMPARATORS[state.sortBy];
  if (!comparator) {
    cards.forEach((card) => {
      card.style.order = "";
    });
    return;
  }
  [...cards].sort(comparator).forEach((card, index) => {
    card.style.order = String(index);
  });
}

function updateChrome(elements: Elements, state: State, visible: number): void {
  elements.reset.disabled = !isDirty(state);
  const total = cardsOf(elements).length;
  elements.count.textContent = visible === total ? `${String(total)} программ` : `Найдено: ${String(visible)} из ${String(total)}`;
}

function hide(state: State, card: HTMLElement): void {
  if (card.classList.contains("is-hidden")) {
    return;
  }
  card.classList.remove("is-entering", "is-shown");
  card.classList.add("is-leaving");
  window.setTimeout(() => {
    if (!matches(state, card)) {
      card.classList.add("is-hidden");
      card.classList.remove("is-leaving");
    }
  }, leaveMs);
}

function show(state: State, card: HTMLElement, delay: number): boolean {
  const wasHidden = card.classList.contains("is-hidden") || card.classList.contains("is-leaving");
  card.classList.remove("is-hidden", "is-leaving");
  if (!wasHidden || reduceMotion) {
    card.classList.remove("is-entering");
    return false;
  }
  card.classList.add("is-entering");
  void card.offsetWidth;
  window.setTimeout(() => {
    if (matches(state, card)) {
      card.classList.remove("is-entering");
    }
  }, delay);
  return true;
}

function applyFilters(elements: Elements, state: State): void {
  const cards = cardsOf(elements);
  applySort(state, cards);
  const shown = cards.filter((card) => matches(state, card));
  cards.filter((card) => !shown.includes(card)).forEach((card) => {
    hide(state, card);
  });
  let delay = 0;
  shown.forEach((card) => {
    if (show(state, card, delay)) {
      delay += enterStaggerMs;
    }
  });
  const isEmpty = shown.length === 0;
  const wasEmpty = elements.empty.classList.contains("visible");
  elements.empty.classList.toggle("visible", isEmpty);
  updateChrome(elements, state, shown.length);
  if (isEmpty && !wasEmpty) {
    elements.reset.scrollIntoView({ block: "nearest", behavior: reduceMotion ? "auto" : "smooth" });
  }
}

function activate(row: HTMLElement, target: HTMLElement): void {
  row.querySelectorAll<HTMLElement>(".chip").forEach((chip) => {
    const on = chip === target;
    chip.classList.toggle("active", on);
    chip.setAttribute("aria-pressed", String(on));
  });
}

function allChip(row: HTMLElement): HTMLElement | null {
  return row.querySelector<HTMLElement>(`.chip[data-value="${ALL}"]`);
}

function onChipClick(elements: Elements, state: State, row: HTMLElement, chip: HTMLElement): void {
  const group = row.dataset.group;
  const isAll = chip.dataset.value === ALL;
  const wasActive = chip.classList.contains("active");
  if (!isGroup(group) || (wasActive && isAll)) {
    return;
  }
  const target = wasActive ? allChip(row) : chip;
  if (!target) {
    return;
  }
  activate(row, target);
  state.active[group] = target.dataset.value ?? ALL;
  applyFilters(elements, state);
}

function filterRows(): HTMLElement[] {
  return [...document.querySelectorAll<HTMLElement>(".filters[data-group]")];
}

function bindChips(elements: Elements, state: State): void {
  filterRows().forEach((row) => {
    row.addEventListener("click", (event) => {
      const chip = event.target instanceof Element ? event.target.closest<HTMLElement>(".chip") : null;
      if (chip) {
        onChipClick(elements, state, row, chip);
      }
    });
  });
}

function bindSearch(elements: Elements, state: State): void {
  let timer: number | undefined;
  elements.search.addEventListener("input", () => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => {
      state.query = elements.search.value;
      applyFilters(elements, state);
    }, SEARCH_DELAY_MS);
  });
}

function resetAll(elements: Elements, state: State): void {
  GROUPS.forEach((group) => {
    state.active[group] = ALL;
  });
  state.sortBy = DEFAULT_SORT;
  state.query = "";
  elements.sort.value = DEFAULT_SORT;
  elements.search.value = "";
  filterRows().forEach((row) => {
    const first = row.querySelector<HTMLElement>(".chip");
    if (first) {
      activate(row, first);
    }
  });
  applyFilters(elements, state);
  elements.search.focus();
}

function applyGroupFromUrl(params: URLSearchParams, state: State, row: HTMLElement): boolean {
  const group = row.dataset.group;
  const wanted = isGroup(group) ? params.get(group) : null;
  const chip = [...row.querySelectorAll<HTMLElement>(".chip")].find((item) => item.dataset.value === wanted);
  if (!isGroup(group) || !wanted || !chip) {
    return false;
  }
  activate(row, chip);
  state.active[group] = wanted;
  return true;
}

function applyStateFromUrl(elements: Elements, state: State): boolean {
  const params = new URLSearchParams(window.location.search);
  let touched = filterRows()
    .map((row) => applyGroupFromUrl(params, state, row))
    .some(Boolean);
  const query = params.get("q");
  if (query) {
    state.query = query;
    elements.search.value = query;
    touched = true;
  }
  const sort = params.get("sort");
  if (sort && [...elements.sort.options].some((option) => option.value === sort)) {
    state.sortBy = sort;
    elements.sort.value = sort;
    touched = true;
  }
  return touched;
}

function findElements(): Elements | null {
  const grid = document.getElementById("grid");
  const empty = document.getElementById("empty");
  const search = document.getElementById("searchInput");
  const reset = document.getElementById("resetFilters");
  const count = document.getElementById("resultCount");
  const sort = document.getElementById("sortSelect");
  if (
    !grid ||
    !empty ||
    !count ||
    !(search instanceof HTMLInputElement) ||
    !(reset instanceof HTMLButtonElement) ||
    !(sort instanceof HTMLSelectElement)
  ) {
    return null;
  }
  return { grid, empty, search, reset, count, sort };
}

export function setupCatalogFilters(): void {
  const elements = findElements();
  if (!elements) {
    return;
  }
  const state: State = { active: { type: ALL, format: ALL, sphere: ALL, duration: ALL }, sortBy: DEFAULT_SORT, query: "" };
  bindChips(elements, state);
  bindSearch(elements, state);
  elements.sort.addEventListener("change", () => {
    state.sortBy = elements.sort.value;
    applyFilters(elements, state);
  });
  elements.reset.addEventListener("click", () => {
    resetAll(elements, state);
  });
  if (applyStateFromUrl(elements, state)) {
    applyFilters(elements, state);
  } else {
    updateChrome(elements, state, cardsOf(elements).length);
  }
}
