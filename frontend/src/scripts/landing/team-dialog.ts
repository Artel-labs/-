import { closeButton, element, openDialog } from "../dialog";
import { attachSheet } from "../sheet-gesture";

const HSE_PAGE = /^https:\/\/([a-z0-9-]+\.)*hse\.ru\//i;

interface TaughtProgram {
  t: string;
  h: string;
}

interface TeacherData {
  name: string;
  about?: string;
  programs?: TaughtProgram[];
  url?: string;
}

function parse(card: Element): TeacherData | null {
  try {
    const data = JSON.parse(card.getAttribute("data-dpo-teacher") ?? "{}") as TeacherData;
    return data.name ? data : null;
  } catch {
    return null;
  }
}

function programList(programs: TaughtProgram[]): HTMLUListElement {
  const list = element("ul", "dpo-team-programs");
  programs.forEach((program) => {
    const item = element("li");
    const link = element("a", "", program.t);
    link.href = program.h;
    item.appendChild(link);
    list.appendChild(item);
  });
  return list;
}

function hsePageLink(url: string): HTMLAnchorElement {
  const link = element("a", "dpo-team-hse", "Личная страница на hse.ru");
  link.href = url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  return link;
}

function content(data: TeacherData, close: HTMLButtonElement): HTMLElement {
  const dialog = element("div", "dpo-team");
  dialog.setAttribute("role", "dialog");
  dialog.setAttribute("aria-modal", "true");
  dialog.setAttribute("aria-labelledby", "dpo-team-title");
  const title = element("h2", "", data.name);
  title.id = "dpo-team-title";
  dialog.append(close, title);
  if (data.about) {
    dialog.appendChild(element("p", "dpo-team-about", data.about));
  }
  if (data.programs?.length) {
    dialog.append(element("p", "dpo-team-label", "Ведёт программы"), programList(data.programs));
  }
  if (data.url && HSE_PAGE.test(data.url)) {
    dialog.appendChild(hsePageLink(data.url));
  }
  return dialog;
}

function open(card: Element, opener: Element): void {
  const data = parse(card);
  if (!data) {
    return;
  }
  const close = closeButton("dpo-team-close", "Закрыть окно");
  const sheet = content(data, close);
  const backdrop = element("div", "dpo-team-backdrop");
  backdrop.appendChild(sheet);
  const dialog = openDialog({ backdrop, initialFocus: close, opener });
  close.addEventListener("click", () => {
    dialog.close();
  });
  attachSheet({ root: backdrop, sheet, grip: ".dpo-team h2, .dpo-team-label", onClose: () => dialog.close() });
}

export function setupTeamDialog(): void {
  document.addEventListener("click", (event) => {
    const target = event.target instanceof Element ? event.target : null;
    const card = target?.closest("[data-dpo-teacher]");
    if (!card || target?.closest("a")) {
      return;
    }
    event.preventDefault();
    open(card, target?.closest(".dpo-teacher-more") ?? card.querySelector(".dpo-teacher-more") ?? card);
  });
}
