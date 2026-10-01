import type { BotProgram } from "./types";

const META_SEPARATOR = " · ";
const DEFAULT_MORE = "Подробнее на сайте";

export function node<K extends keyof HTMLElementTagNameMap>(tag: K, className = "", text = ""): HTMLElementTagNameMap[K] {
  const element = document.createElement(tag);
  if (className) {
    element.className = className;
  }
  if (text) {
    element.textContent = text;
  }
  return element;
}

export function programCard(program: BotProgram): HTMLElement {
  const link = node("a", "", program.title);
  link.href = program.url;
  const meta = [program.format_label, program.hours, program.price_label, program.start].filter(Boolean).join(META_SEPARATOR);
  const card = node("article", "dpo-bot-card");
  card.append(link, node("p", "", meta));
  return card;
}

export function moreLink(anchor: string, label = DEFAULT_MORE): HTMLAnchorElement {
  const link = node("a", "dpo-bot-more", label);
  link.href = anchor;
  return link;
}

export function applyButton(): HTMLButtonElement {
  const button = node("button", "dpo-bot-apply", "Подать заявку");
  button.type = "button";
  button.dataset.application = "";
  return button;
}

export function choiceButton(text: string, onClick: () => void): HTMLButtonElement {
  const button = node("button", "", text);
  button.type = "button";
  button.addEventListener("click", onClick);
  return button;
}

export function typingDots(): HTMLElement {
  const dots = node("div", "dpo-bot-typing");
  dots.setAttribute("aria-hidden", "true");
  dots.append(node("i"), node("i"), node("i"));
  return dots;
}
