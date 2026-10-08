import { findDropdowns, nameOf, setupDropdowns, showSelection, valuesOf, type Dropdown } from "./catalog-dropdowns";
import { parseValues, passes, without } from "./catalog-selection";
import { setupFilterSheet, showSheetTotal, type Selection } from "./catalog-sheet";
import { renderTags, type FilterTag } from "./catalog-tags";
import { emptyCrowToggle } from "./crow/inline";

const GROUPS = ["type", "format", "sphere", "duration"] as const;
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
  tags: HTMLElement;
  dropdowns: Dropdown[];
  syncEmptyCrow: (isEmpty: boolean) => void;
}

interface State {
  active: Record<Group, string[]>;
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
  const fits = GROUPS.every((group) => passes(state.active[group], card.dataset[group]));
  const query = state.query.trim().toLowerCase();
  return fits && (!query || (card.dataset.search ?? "").toLowerCase().includes(query));
}

function isDirty(state: State): boolean {
  return GROUPS.some((group) => state.active[group].length > 0) || state.query.trim() !== "" || state.sortBy !== DEFAULT_SORT;
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
  elements.count.textContent = visible === total ? (elements.count.dataset.totalLabel ?? "") : `Найдено: ${String(visible)} из\u00a0${String(total)}`;
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
  elements.syncEmptyCrow(isEmpty);
  updateChrome(elements, state, shown.length);
  if (isEmpty && !wasEmpty) {
    elements.reset.scrollIntoView({ block: "nearest", behavior: reduceMotion ? "auto" : "smooth" });
  }
}

function tagsOf(elements: Elements, state: State): FilterTag[] {
  return elements.dropdowns.flatMap((dropdown) =>
    isGroup(dropdown.group)
      ? state.active[dropdown.group].map((value) => ({ group: dropdown.group, value, name: nameOf(dropdown, value) }))
      : [],
  );
}

function refresh(elements: Elements, state: State): void {
  elements.dropdowns.forEach((dropdown) => {
    if (isGroup(dropdown.group)) {
      showSelection(dropdown, state.active[dropdown.group]);
    }
  });
  showSheetTotal(GROUPS.reduce((total, group) => total + state.active[group].length, 0));
  renderTags(elements.tags, tagsOf(elements, state), {
    remove: (tag) => {
      if (isGroup(tag.group)) {
        state.active[tag.group] = without(state.active[tag.group], tag.value);
        refresh(elements, state);
      }
    },
    reset: () => {
      resetAll(elements, state);
    },
  });
  applyFilters(elements, state);
}

function draftOf(state: State, selection: Selection): State {
  const active = { ...state.active };
  GROUPS.forEach((group) => {
    active[group] = selection[group] ?? active[group];
  });
  return { ...state, active };
}

function bindSheet(elements: Elements, state: State): void {
  setupFilterSheet(elements.dropdowns, {
    applied: (group) => (isGroup(group) ? state.active[group] : []),
    preview: (selection) => {
      const draft = draftOf(state, selection);
      return cardsOf(elements).filter((card) => matches(draft, card)).length;
    },
    apply: (selection) => {
      state.active = draftOf(state, selection).active;
      refresh(elements, state);
    },
  });
}

function bindDropdowns(elements: Elements, state: State): void {
  setupDropdowns(elements.dropdowns, {
    applied: (group) => (isGroup(group) ? state.active[group] : []),
    apply: (group, values) => {
      if (isGroup(group)) {
        state.active[group] = values;
        refresh(elements, state);
      }
    },
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
    state.active[group] = [];
  });
  state.sortBy = DEFAULT_SORT;
  state.query = "";
  elements.sort.value = DEFAULT_SORT;
  elements.search.value = "";
  refresh(elements, state);
  elements.search.focus();
}

function applyGroupFromUrl(params: URLSearchParams, state: State, dropdown: Dropdown): boolean {
  if (!isGroup(dropdown.group)) {
    return false;
  }
  state.active[dropdown.group] = parseValues(params.get(dropdown.group), valuesOf(dropdown));
  return state.active[dropdown.group].length > 0;
}

function applyStateFromUrl(elements: Elements, state: State): boolean {
  const params = new URLSearchParams(window.location.search);
  let touched = elements.dropdowns.map((dropdown) => applyGroupFromUrl(params, state, dropdown)).some(Boolean);
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
  const tags = document.getElementById("filterTags");
  if (
    !grid ||
    !tags ||
    !empty ||
    !count ||
    !(search instanceof HTMLInputElement) ||
    !(reset instanceof HTMLButtonElement) ||
    !(sort instanceof HTMLSelectElement)
  ) {
    return null;
  }
  return { grid, empty, search, reset, count, sort, tags, dropdowns: findDropdowns(), syncEmptyCrow: emptyCrowToggle(empty) };
}

export function setupCatalogFilters(): void {
  const elements = findElements();
  if (!elements) {
    return;
  }
  const state: State = { active: { type: [], format: [], sphere: [], duration: [] }, sortBy: DEFAULT_SORT, query: "" };
  bindDropdowns(elements, state);
  bindSheet(elements, state);
  bindSearch(elements, state);
  elements.sort.addEventListener("change", () => {
    state.sortBy = elements.sort.value;
    applyFilters(elements, state);
  });
  elements.reset.addEventListener("click", () => {
    resetAll(elements, state);
  });
  if (applyStateFromUrl(elements, state)) {
    refresh(elements, state);
  } else {
    updateChrome(elements, state, cardsOf(elements).length);
  }
}
