import type { TgProgram } from "../../lib/tg";
import type { Context, Direction } from "./context";
import { filterPrograms, formatPrice } from "./core.ts";
import { h, hseLockup, picture, searchIcon } from "./dom";

const MAX_CASCADE_STEP = 7;
const ALL = "all";

function programCard(program: TgProgram, index: number): HTMLButtonElement {
  const price = formatPrice(program.price);
  const card = h("button", { class: "card", type: "button", "data-id": program.id }, [
    h("span", { class: "cover" }, [
      picture(program.thumb),
      h("span", { class: "tags" }, [program.badge && h("span", { class: "tag", text: program.badge }), program.format && h("span", { class: "tag", text: program.format })]),
    ]),
    h("span", { class: "card-body" }, [
      h("span", { class: "card-title", text: program.title }),
      h("span", { class: "meta" }, [
        price ? h("span", { class: "price" }, [price, program.old_price ? h("s", { text: formatPrice(program.old_price) }) : null]) : h("span"),
        program.start_label ? h("span", { text: program.start_label }) : null,
      ]),
    ]),
  ]);
  card.style.setProperty("--i", String(Math.min(index, MAX_CASCADE_STEP)));
  return card;
}

function chipRow(context: Context): HTMLElement {
  const chips = h("div", { class: "chips", role: "group", "aria-label": "Сферы" });
  [{ id: ALL, title: "Все", count: context.data.programs.length }, ...context.data.spheres].forEach((sphere) => {
    chips.append(
      h("button", { class: "chip", type: "button", "data-sphere": sphere.id, "aria-pressed": String(context.state.sphere === sphere.id) }, [
        sphere.title,
        h("small", { text: String(sphere.count) }),
      ]),
    );
  });
  return chips;
}

export function listScreen(context: Context, direction: Direction): HTMLElement {
  const { state } = context;
  const cards = h("div", { class: "cards" });
  const chips = chipRow(context);
  const search = h("input", { type: "search", placeholder: "Название или тема", "aria-label": "Поиск программ", enterkeyhint: "search" });
  search.value = state.query;

  const fill = (cascade: boolean): void => {
    const items = filterPrograms(context.data.programs, state.sphere, state.query);
    cards.classList.toggle("cascade", cascade);
    cards.textContent = "";
    if (!items.length) {
      cards.append(h("p", { class: "empty", text: "Ничего не нашлось. Попробуйте другое слово или сферу." }));
      return;
    }
    cards.append(...items.map(programCard));
  };

  chips.addEventListener("click", (event) => {
    const chip = event.target instanceof Element ? event.target.closest<HTMLElement>(".chip") : null;
    if (!chip) {
      return;
    }
    state.sphere = chip.dataset.sphere ?? ALL;
    Array.from(chips.children).forEach((node) => {
      node.setAttribute("aria-pressed", String(node === chip));
    });
    fill(false);
  });
  search.addEventListener("input", () => {
    state.query = search.value;
    fill(false);
  });
  cards.addEventListener("click", (event) => {
    const card = event.target instanceof Element ? event.target.closest<HTMLElement>(".card") : null;
    if (!card) {
      return;
    }
    state.programId = card.dataset.id ?? null;
    context.go("program");
  });

  fill(direction !== "back");
  context.bridge.setMain(null);
  return h("section", { "aria-label": "Программы" }, [
    hseLockup(context.bridge),
    h("h1", { class: "h1", text: "Программы Центра ДПО факультета права" }),
    h("label", { class: "search" }, [searchIcon(), search]),
    chips,
    cards,
  ]);
}
