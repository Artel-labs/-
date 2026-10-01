import type { Chat } from "./chat";
import { formatPrice, introFor, pickBy, priceRange, sphereList, upcoming, type Reply } from "./reply.ts";
import type { BotData } from "./types";
import { applyButton, choiceButton, moreLink, node } from "./view";

const GAP_TEXT = "Об этом на сайте не написано, а придумывать я не стану. Оставьте заявку – ответит учебный офис.";
const NOTHING_FOUND = "Такого не нашла. Вот что стартует ближе всего:";
const WEAK_MATCH = "Точного совпадения нет, вот близкое по теме:";
const EXTRA_INTRO = "Ещё нашла программы по теме:";
const CATALOG_URL = "/catalog";
const TYPE_CHOICES: [string, string][] = [
  ["ПК", "Повышение квалификации"],
  ["ПП", "Переподготовка"],
];
const SHOWN_PROGRAMS = 5;
const NEAREST_PROGRAMS = 3;

function renderExtra(chat: Chat, reply: { extra?: BotData["programs"] }): void {
  if (!reply.extra?.length) {
    return;
  }
  chat.say(EXTRA_INTRO);
  chat.cards(reply.extra);
}

function sayLines(chat: Chat, text: string): void {
  text.split("\n").forEach((line) => {
    chat.say(line);
  });
}

export function renderReply(chat: Chat, reply: Reply): void {
  switch (reply.kind) {
    case "programs":
      chat.say(reply.intro);
      chat.cards(reply.programs);
      return;
    case "programs-weak":
      chat.say(WEAK_MATCH);
      chat.cards(reply.programs);
      return;
    case "duration":
      sayLines(chat, reply.text);
      chat.add(moreLink(reply.anchor));
      renderExtra(chat, reply);
      return;
    case "answer":
      sayLines(chat, reply.answer.text);
      if (reply.answer.note) {
        chat.say(reply.answer.note);
      }
      chat.add(moreLink(reply.answer.anchor));
      renderExtra(chat, reply);
      return;
    case "gap":
      chat.say(GAP_TEXT);
      chat.add(applyButton());
      return;
    case "none":
      chat.say(NOTHING_FOUND);
      chat.cards(reply.programs);
      chat.add(applyButton());
  }
}

function renderPicked(chat: Chat, data: BotData, field: "sphere" | "type", value: string): void {
  const matched = pickBy(data.programs, field, value);
  if (!matched.length) {
    chat.say(NOTHING_FOUND);
    chat.cards(upcoming(data.programs, NEAREST_PROGRAMS));
    chat.add(applyButton());
    return;
  }
  chat.say(introFor("filter", matched.length));
  chat.cards(matched.slice(0, SHOWN_PROGRAMS));
}

function pickButton(chat: Chat, data: BotData, field: "sphere" | "type", value: string, label: string): HTMLButtonElement {
  return choiceButton(label, () => {
    chat.mine(label);
    chat.respond(() => {
      renderPicked(chat, data, field, value);
    });
  });
}

export function renderPickProgram(chat: Chat, data: BotData): void {
  chat.say("Выберите сферу или тип программы:");
  const row = node("div", "dpo-bot-hints");
  row.append(
    ...sphereList(data.programs).map((sphere) => pickButton(chat, data, "sphere", sphere, sphere)),
    ...TYPE_CHOICES.map(([type, label]) => pickButton(chat, data, "type", type, label)),
  );
  chat.add(row);
  chat.scrollDown();
}

export function renderUpcomingStarts(chat: Chat, data: BotData): void {
  const list = upcoming(data.programs, SHOWN_PROGRAMS).filter((program) => program.start_iso || program.start);
  if (!list.length) {
    chat.say("Дат старта в каталоге сейчас нет.");
    chat.scrollDown();
    return;
  }
  chat.say(list.length === 1 ? "Ближайший старт:" : "Вот ближайшие старты:");
  chat.cards(list);
  chat.scrollDown();
}

export function renderPriceRange(chat: Chat, data: BotData): void {
  const range = priceRange(data.programs);
  if (!range) {
    chat.say("Цены сейчас не в каталоге – загляните в разделы программ.");
    chat.scrollDown();
    return;
  }
  chat.say(`Программы стоят от ${formatPrice(range.min)} до ${formatPrice(range.max)}.`);
  chat.say("Могу отобрать по цене – напишите, например, «до 30000» или «от 50000».");
  chat.add(moreLink(CATALOG_URL, "Открыть каталог"));
  chat.scrollDown();
}
