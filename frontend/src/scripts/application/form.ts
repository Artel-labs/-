import { element } from "../dialog";
import { CORPORATE, OTHER_SOURCE, PERSONAL, PRIVACY_URL, SOURCES, SUBMIT_LABEL, TOPICS } from "./constants";
import { errorBox, inputField, row, selectField } from "./fields";

export interface FormHandlers {
  onTopic: (topic: string) => void;
  onKind: (kind: string) => void;
}

function topicField(handlers: FormHandlers): HTMLDivElement {
  const { wrapper, select } = selectField("dpo-app-topic", "topic", "Тема обращения", TOPICS);
  select.addEventListener("change", () => {
    handlers.onTopic(select.value);
  });
  return wrapper;
}

function kindField(handlers: FormHandlers): HTMLDivElement {
  const { wrapper, select } = selectField("dpo-app-kind", "applicantType", "Кто подаёт заявку", [
    [PERSONAL, "За себя"],
    [CORPORATE, "От организации — обучение сотрудников"],
  ]);
  wrapper.id = "dpo-app-kind-wrap";
  select.addEventListener("change", () => {
    handlers.onKind(select.value);
  });
  return wrapper;
}

function corporateBlock(): HTMLDivElement {
  const block = row(
    inputField({ name: "employeesCount", text: "Сколько сотрудников обучить", type: "text", placeholder: "например: 8 или 10–15" }),
    inputField({ name: "timeframe", text: "Желаемые сроки", type: "text", placeholder: "например: октябрь—декабрь" }),
  );
  block.id = "dpo-app-corp";
  block.hidden = true;
  return block;
}

function programField(): HTMLDivElement {
  const { wrapper, select } = selectField("dpo-app-program", "program", "Программа", [["", "Ещё не выбрал(а) — помогите подобрать"]]);
  wrapper.id = "dpo-app-program-wrap";
  wrapper.hidden = true;
  select.setAttribute("aria-describedby", "dpo-app-program-err");
  wrapper.appendChild(errorBox("program"));
  return wrapper;
}

function sourcesBlock(): HTMLElement[] {
  const { wrapper, select } = selectField("dpo-app-sources", "sources", "Как вы узнали о нас?", [["", "Не выбрано"], ...SOURCES]);
  const other = inputField({ name: "sourceOther", text: "Уточните, откуда узнали", type: "text" });
  other.id = "dpo-app-other-wrap";
  other.hidden = true;
  other.querySelector(".dpo-app-err")?.remove();
  other.querySelector("input")?.removeAttribute("aria-describedby");
  select.addEventListener("change", () => {
    const isOther = select.value === OTHER_SOURCE;
    other.hidden = !isOther;
    if (isOther) {
      other.querySelector("input")?.focus();
    }
  });
  return [wrapper, other];
}

function checkbox(name: string, text: string): HTMLLabelElement {
  const label = element("label", "dpo-app-check");
  const input = element("input");
  input.type = "checkbox";
  input.name = name;
  label.append(input, element("span", "", text));
  return label;
}

function moreDetails(): HTMLDetailsElement {
  const details = element("details", "dpo-app-more");
  const body = element("div", "dpo-app-more-body");
  body.append(
    row(
      inputField({ name: "position", text: "Должность", type: "text", autocomplete: "organization-title" }),
      inputField({ name: "company", text: "Место работы", type: "text", autocomplete: "organization" }),
    ),
    ...sourcesBlock(),
    checkbox("noAnnouncements", "Не присылать анонсы новых программ и мероприятий Центра ДПО факультета права"),
  );
  details.append(element("summary", "", "Ещё о себе: должность, место работы, откуда узнали"), body);
  return details;
}

function commentField(): HTMLDivElement {
  const wrapper = element("div", "dpo-app-field");
  const label = element("label", "", "Комментарий или вопрос");
  label.htmlFor = "dpo-app-comment";
  const textarea = element("textarea");
  textarea.id = "dpo-app-comment";
  textarea.name = "comment";
  textarea.rows = 3;
  textarea.placeholder = "Например: интересует корпоративный формат для группы из восьми юристов";
  wrapper.append(label, textarea);
  return wrapper;
}

function consentField(): HTMLElement[] {
  const label = element("label", "dpo-app-consent");
  const input = element("input");
  input.type = "checkbox";
  input.name = "consent";
  input.id = "dpo-app-consent";
  input.setAttribute("aria-describedby", "dpo-app-consent-err");
  const privacy = element("a", "", "Политикой обработки персональных данных");
  privacy.href = PRIVACY_URL;
  privacy.target = "_blank";
  privacy.rel = "noopener";
  const text = element("span");
  text.append(
    "Я подтверждаю, что ознакомился с ",
    privacy,
    ", и даю согласие на обработку моих персональных данных для рассмотрения заявки. ",
    element("span", "req", "*"),
  );
  label.append(input, text);
  return [label, errorBox("consent")];
}

function trapField(): HTMLDivElement {
  const trap = element("div", "dpo-app-trap");
  trap.setAttribute("aria-hidden", "true");
  const label = element("label", "", "Не заполняйте это поле");
  label.htmlFor = "dpo-app-website";
  const input = element("input");
  input.type = "text";
  input.id = "dpo-app-website";
  input.name = "website";
  input.tabIndex = -1;
  input.autocomplete = "off";
  trap.append(label, input);
  return trap;
}

function statusBlock(): HTMLDivElement {
  const block = element("div", "dpo-app-error");
  const crow = element("div", "dpo-app-error-crow");
  crow.setAttribute("aria-hidden", "true");
  const status = element("p", "dpo-app-status");
  status.setAttribute("role", "status");
  status.setAttribute("aria-live", "polite");
  block.append(crow, status);
  return block;
}

export function buildForm(handlers: FormHandlers): HTMLFormElement {
  const form = element("form", "dpo-app-form");
  form.noValidate = true;
  const submit = element("button", "dpo-app-submit", SUBMIT_LABEL);
  submit.type = "submit";
  form.append(
    topicField(handlers),
    kindField(handlers),
    corporateBlock(),
    programField(),
    row(
      inputField({ name: "lastName", text: "Фамилия", type: "text", required: true, autocomplete: "family-name" }),
      inputField({ name: "firstName", text: "Имя", type: "text", required: true, autocomplete: "given-name" }),
    ),
    row(
      inputField({ name: "phone", text: "Телефон", type: "tel", required: true, autocomplete: "tel" }),
      inputField({ name: "email", text: "Электронная почта", type: "email", required: true, autocomplete: "email" }),
    ),
    moreDetails(),
    commentField(),
    ...consentField(),
    trapField(),
    submit,
    statusBlock(),
    element("p", "dpo-app-note", "Мы свяжемся с вами по телефону или почте. Данные не передаются третьим лицам."),
  );
  return form;
}
