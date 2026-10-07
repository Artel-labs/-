import { element } from "../dialog";
import { ADS_CHECK, ADS_CONSENT_URL, ANONYMOUS_HINT, CONSENT_CHECK, CONSENT_URL, CORPORATE, PERSONAL, PERSONAL_CLASS, SENSITIVE_HINT, SUBMIT_LABEL, TOPICS } from "./constants";
import { errorBox, inputField, row, selectField } from "./fields";
import { PRIVACY_POLICY_URL } from "../../lib/brand";

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
  const { wrapper, select } = selectField("dpo-app-kind", "applicantType", "Кто будет обучаться", [
    [PERSONAL, "Частное лицо"],
    [CORPORATE, "Сотрудник организации"],
  ]);
  wrapper.id = "dpo-app-kind-wrap";
  select.addEventListener("change", () => {
    handlers.onKind(select.value);
  });
  return wrapper;
}

function corporateBlock(): HTMLDivElement {
  const block = element("div");
  block.append(
    inputField({ name: "company", text: "Организация-заказчик", type: "text", autocomplete: "organization" }),
    row(
      inputField({ name: "employeesCount", text: "Сколько сотрудников обучить", type: "text", placeholder: "например: 8 или 10–15" }),
      inputField({ name: "timeframe", text: "Желаемые сроки", type: "text", placeholder: "например: октябрь—декабрь" }),
    ),
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

function personal<T extends HTMLElement>(node: T): T {
  node.classList.add(PERSONAL_CLASS);
  return node;
}

function commentField(): HTMLDivElement {
  const wrapper = element("div", "dpo-app-field");
  const label = element("label", "", "Комментарий или вопрос");
  label.htmlFor = "dpo-app-comment";
  const textarea = element("textarea");
  textarea.id = "dpo-app-comment";
  textarea.name = "comment";
  textarea.rows = 3;
  textarea.setAttribute("aria-describedby", "dpo-app-comment-note dpo-app-comment-hint dpo-app-comment-err");
  const note = element("p", "dpo-app-hint", SENSITIVE_HINT);
  note.id = "dpo-app-comment-note";
  const hint = element("p", "dpo-app-hint", ANONYMOUS_HINT);
  hint.id = "dpo-app-comment-hint";
  hint.hidden = true;
  textarea.placeholder = "Например: интересует корпоративный формат для группы из восьми юристов";
  wrapper.append(label, textarea, note, hint, errorBox("comment"));
  return wrapper;
}

function newTabLink(text: string, href: string): HTMLAnchorElement {
  const link = element("a", "", text);
  link.href = href;
  link.target = "_blank";
  link.rel = "noopener";
  return link;
}

function adsConsentField(): HTMLLabelElement {
  const label = element("label", "dpo-app-check");
  const input = element("input");
  input.type = "checkbox";
  input.name = "adsConsent";
  input.id = "dpo-app-adsConsent";
  const text = element("span");
  text.append(ADS_CHECK.before, newTabLink(ADS_CHECK.consent, ADS_CONSENT_URL), ADS_CHECK.after);
  label.append(input, text);
  return label;
}

function consentField(): HTMLElement[] {
  const label = element("label", "dpo-app-consent");
  const input = element("input");
  input.type = "checkbox";
  input.name = "consent";
  input.id = "dpo-app-consent";
  input.setAttribute("aria-describedby", "dpo-app-consent-err");
  const text = element("span");
  text.append(
    CONSENT_CHECK.before,
    newTabLink(CONSENT_CHECK.regulation, PRIVACY_POLICY_URL),
    CONSENT_CHECK.middle,
    newTabLink(CONSENT_CHECK.consent, CONSENT_URL),
    CONSENT_CHECK.after,
    " ",
    element("span", "req", "*"),
  );
  label.append(input, text);
  return [personal(label), personal(errorBox("consent"))];
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
    personal(row(
      inputField({ name: "lastName", text: "Фамилия", type: "text", required: true, autocomplete: "family-name" }),
      inputField({ name: "firstName", text: "Имя", type: "text", required: true, autocomplete: "given-name" }),
    )),
    personal(row(
      inputField({ name: "phone", text: "Телефон", type: "tel", required: true, autocomplete: "tel" }),
      inputField({ name: "email", text: "Электронная почта", type: "email", required: true, autocomplete: "email" }),
    )),
    commentField(),
    personal(adsConsentField()),
    ...consentField(),
    trapField(),
    submit,
    statusBlock(),
    personal(element("p", "dpo-app-note", "Мы свяжемся с вами по телефону или почте. Данные не передаются третьим лицам.")),
  );
  return form;
}
