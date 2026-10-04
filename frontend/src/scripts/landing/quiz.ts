import { closeButton, element, openDialog, type Dialog } from "../dialog";
import { attachSheet, type SheetControl } from "../sheet-gesture";

const CATALOG_PATH = "/catalog";
const UNDECIDED = "Пока не определился";

interface Question {
  group: string;
  title: string;
  options: [string, string][];
}

function questions(branches: string[]): Question[] {
  return [
    {
      group: "q",
      title: "Какая отрасль или область права вас интересует?",
      options: [["", UNDECIDED], ...branches.map((branch): [string, string] => [branch, branch])],
    },
    {
      group: "type",
      title: "Какой документ об обучении вам нужен?",
      options: [
        ["", UNDECIDED],
        ["ПК", "Удостоверение о повышении квалификации"],
        ["ПП", "Диплом о профессиональной переподготовке"],
      ],
    },
    {
      group: "format",
      title: "Как вам удобно учиться?",
      options: [
        ["", "Любой формат"],
        ["online", "Онлайн"],
        ["offline", "Очно"],
        ["mixed", "Смешанный"],
        ["hybrid", "Гибридный"],
      ],
    },
  ];
}

function selectField(question: Question): HTMLElement {
  const field = element("div", "dpo-quiz-field");
  const label = element("label", "", question.title);
  label.htmlFor = "dpoQuizBranch";
  const select = element("select", "dpo-quiz-select");
  select.id = "dpoQuizBranch";
  select.name = `dpo-quiz-${question.group}`;
  question.options.forEach(([value, text]) => {
    const option = element("option", "", text);
    option.value = value;
    select.appendChild(option);
  });
  field.append(label, select);
  return field;
}

function radioGroup(question: Question): HTMLElement {
  const fieldset = element("fieldset");
  const options = element("div", "dpo-quiz-opts");
  question.options.forEach(([value, text], index) => {
    const label = element("label", "dpo-quiz-opt");
    const input = element("input");
    input.type = "radio";
    input.name = `dpo-quiz-${question.group}`;
    input.value = value;
    input.checked = index === 0;
    label.append(input, element("span", "", text));
    options.appendChild(label);
  });
  fieldset.append(element("legend", "", question.title), options);
  return fieldset;
}

function catalogUrl(form: HTMLFormElement, list: Question[]): string {
  const data = new FormData(form);
  const params = new URLSearchParams();
  list.forEach((question) => {
    const value = data.get(`dpo-quiz-${question.group}`);
    if (typeof value === "string" && value) {
      params.set(question.group, value);
    }
  });
  const query = params.toString();
  return query ? `${CATALOG_PATH}?${query}` : CATALOG_PATH;
}

function build(branches: string[]): { backdrop: HTMLElement; sheet: HTMLElement; close: HTMLButtonElement } {
  const list = questions(branches);
  const backdrop = element("div", "dpo-quiz-backdrop");
  const sheet = element("div", "dpo-quiz");
  sheet.setAttribute("role", "dialog");
  sheet.setAttribute("aria-modal", "true");
  sheet.setAttribute("aria-labelledby", "dpoQuizTitle");
  const close = closeButton("dpo-quiz-close", "Закрыть опрос");
  const title = element("h2", "", "Подберём программу");
  title.id = "dpoQuizTitle";
  const form = element("form");
  form.append(...list.map((question) => (question.group === "q" ? selectField(question) : radioGroup(question))));
  const submit = element("button", "dpo-quiz-submit", "Показать программы");
  submit.type = "submit";
  form.appendChild(submit);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    window.location.href = catalogUrl(form, list);
  });
  sheet.append(
    close,
    title,
    element("p", "dpo-quiz-sub", "Три вопроса — и вы увидите программы по интересующей области права, документу и формату обучения."),
    form,
  );
  backdrop.appendChild(sheet);
  return { backdrop, sheet, close };
}

export function setupQuiz(): void {
  let built: { backdrop: HTMLElement; sheet: HTMLElement; close: HTMLButtonElement } | null = null;
  let sheetControl: SheetControl | null = null;
  let dialog: Dialog | null = null;
  document.addEventListener("click", (event) => {
    const trigger = event.target instanceof Element ? event.target.closest<HTMLElement>("[data-quiz]") : null;
    if (!trigger || dialog) {
      return;
    }
    event.preventDefault();
    if (!built) {
      const parts = build(JSON.parse(trigger.dataset.quizBranches ?? "[]") as string[]);
      built = parts;
      parts.close.addEventListener("click", () => dialog?.close());
      sheetControl = attachSheet({ root: parts.backdrop, sheet: parts.sheet, grip: "#dpoQuizTitle", onClose: () => dialog?.close() });
    }
    sheetControl?.reset();
    const firstField = built.sheet.querySelector<HTMLElement>("select, input") ?? built.close;
    dialog = openDialog({ backdrop: built.backdrop, initialFocus: firstField, opener: trigger, onClosed: () => (dialog = null) });
  });
}
