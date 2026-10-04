import type { Context } from "./context";
import { formatPrice, LIMITS, validateApplication, type FieldError, type FieldName } from "./core.ts";
import { h, picture } from "./dom";

type Control = FieldName | "consent";

const FORM_FIELDS: [FieldName, string, string, string][] = [
  ["firstName", "Имя", "given-name", "text"],
  ["lastName", "Фамилия", "family-name", "text"],
  ["phone", "Телефон", "tel", "tel"],
  ["email", "E-mail", "email", "email"],
  ["position", "Должность, если хотите", "organization-title", "text"],
  ["company", "Место работы, если хотите", "organization", "text"],
];
const PRIVACY_URL = "/privacy";

class FormControls {
  readonly inputs = new Map<Control, HTMLInputElement>();
  readonly errors = new Map<Control, HTMLElement>();

  register(name: Control, input: HTMLInputElement): HTMLElement {
    const error = h("span", { class: "field-err", id: `err-${name}`, hidden: true });
    this.inputs.set(name, input);
    this.errors.set(name, error);
    return error;
  }

  clear(name: Control): void {
    const error = this.errors.get(name);
    if (error) {
      error.hidden = true;
      error.textContent = "";
    }
    this.inputs.get(name)?.removeAttribute("aria-invalid");
  }

  clearAll(): void {
    this.errors.forEach((_, name) => {
      this.clear(name);
    });
  }

  show(found: FieldError[]): void {
    found.forEach(({ field, message }) => {
      const error = this.errors.get(field);
      if (error) {
        error.textContent = message;
        error.hidden = false;
      }
      this.inputs.get(field)?.setAttribute("aria-invalid", "true");
    });
    const first = found[0];
    if (first) {
      this.inputs.get(first.field)?.focus();
    }
  }
}

function fieldRow(context: Context, controls: FormControls, [name, label, autocomplete, type]: [FieldName, string, string, string]): HTMLElement {
  const draft = context.state.form;
  const input = h("input", {
    name,
    type,
    autocomplete,
    inputmode: type === "tel" ? "tel" : null,
    maxlength: String(LIMITS[name]),
    "aria-describedby": `err-${name}`,
  });
  input.value = draft[name];
  input.addEventListener("input", () => {
    draft[name] = input.value;
    controls.clear(name);
  });
  const error = controls.register(name, input);
  const hint = name === "firstName" && context.state.nameFromTelegram ? h("span", { class: "field-hint", text: " · из профиля Telegram" }) : null;
  return h("div", { class: "field" }, [h("label", null, [h("span", { class: "field-label" }, [label, hint]), input]), error]);
}

function consentRow(context: Context, controls: FormControls): HTMLElement[] {
  const draft = context.state.form;
  const consent = h("input", { type: "checkbox", name: "consent", "aria-describedby": "err-consent" });
  consent.checked = draft.consent;
  consent.addEventListener("change", () => {
    draft.consent = consent.checked;
    controls.clear("consent");
  });
  const error = controls.register("consent", consent);
  const policy = h("a", { href: PRIVACY_URL, target: "_blank", rel: "noopener", text: "Политикой обработки персональных данных" });
  context.bridge.routeLink(policy);
  const label = h("label", { class: "check" }, [
    consent,
    h("span", null, ["Я подтверждаю, что ознакомился с ", policy, ", и даю согласие на обработку моих персональных данных для рассмотрения заявки."]),
  ]);
  return [label, error];
}

export function formScreen(context: Context): HTMLElement {
  const program = context.program();
  const controls = new FormControls();
  const submit = (): void => {
    controls.clearAll();
    const result = validateApplication(context.state.form);
    if (!result.ok) {
      controls.show(result.errors);
      context.bridge.haptic("error");
      return;
    }
    context.state.submitted = result.values;
    context.bridge.haptic("success");
    context.go("demo");
  };
  const form = h("form", { novalidate: true, "aria-label": "Данные для заявки" }, [
    ...FORM_FIELDS.map((field) => fieldRow(context, controls, field)),
    ...consentRow(context, controls),
  ]);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    submit();
  });
  context.bridge.setMain("Отправить заявку", submit);
  const price = formatPrice(program.price);
  return h("section", { "aria-label": "Заявка" }, [
    h("h1", { class: "h1 h1--sm", text: "Заявка" }),
    h("div", { class: "mini" }, [
      h("span", { class: "mini-img" }, [picture(program.thumb)]),
      h("span", null, [h("b", { text: program.title }), h("small", { text: [price, program.start_label].filter(Boolean).join(" · ") })]),
    ]),
    form,
  ]);
}
