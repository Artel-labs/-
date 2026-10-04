import { element } from "../dialog";
import { CATALOG_URL, PROGRAM_TOPIC, VIBRATION_MS } from "./constants";

const PROGRAM_DONE =
  "Заявка принята. Учебный офис Центра ДПО факультета права свяжется с вами по указанному телефону или почте, чтобы подтвердить участие и рассказать о ближайшем наборе.";
const TOPIC_DONE =
  "Обращение принято и записано. Учебный офис Центра ДПО факультета права прочитает его и свяжется с вами, если потребуется уточнение.";
const PAYMENT_NOTE = "Обычно это занимает один рабочий день. Оплата проходит на стороне НИУ ВШЭ — её реквизиты пришлёт учебный офис.";

function programLine(title: string): HTMLParagraphElement {
  const line = element("p", "dpo-app-done-program", "Заявка на программу ");
  line.appendChild(element("b", "", title));
  return line;
}

function doneBody(topic: string, programTitle: string, crow: HTMLElement): HTMLDivElement {
  const isProgram = topic === PROGRAM_TOPIC;
  const next = element("div", "dpo-app-next");
  const catalog = element("a", "", "Посмотреть другие программы");
  catalog.href = CATALOG_URL;
  next.appendChild(catalog);
  const body = element("div", "dpo-app-done");
  body.append(
    crow,
    ...(isProgram && programTitle ? [programLine(programTitle)] : []),
    element("p", "", isProgram ? PROGRAM_DONE : TOPIC_DONE),
    ...(isProgram ? [element("p", "", PAYMENT_NOTE)] : []),
    next,
  );
  return body;
}

export function showDone(dialog: HTMLElement, topic: string, programTitle: string): HTMLElement {
  dialog.querySelector("form")?.remove();
  dialog.querySelector(".dpo-app-program")?.remove();
  const title = dialog.querySelector("h2");
  if (title) {
    title.textContent = "Спасибо!";
  }
  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    navigator.vibrate?.(VIBRATION_MS);
  }
  const crow = element("div", "dpo-app-done-crow");
  crow.setAttribute("aria-hidden", "true");
  dialog.appendChild(doneBody(topic, programTitle, crow));
  dialog.querySelector<HTMLElement>(".dpo-app-close")?.focus();
  return crow;
}
