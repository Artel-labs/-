import { element } from "../dialog";
import { EMAIL_TYPO, emailLooksValid, phoneProblem } from "../form-rules";

const LIVE_RULES: Record<string, (value: string) => string> = {
  phone: phoneProblem,
  email: (value) => (emailLooksValid(value) ? "" : EMAIL_TYPO),
};

export function errorBox(name: string): HTMLParagraphElement {
  const box = element("p", "dpo-app-err");
  box.id = `dpo-app-${name}-err`;
  return box;
}

export function markInvalid(input: HTMLElement, message: string): void {
  if (message) {
    input.setAttribute("aria-invalid", "true");
  } else {
    input.removeAttribute("aria-invalid");
  }
}

function liveCheck(input: HTMLInputElement): void {
  const rule = LIVE_RULES[input.name];
  const box = document.getElementById(`dpo-app-${input.name}-err`);
  if (!rule || !box) {
    return;
  }
  const value = input.value.trim();
  const message = value ? rule(value) : "";
  box.textContent = message;
  markInvalid(input, message);
}

function label(target: string, text: string, required: boolean): HTMLLabelElement {
  const node = element("label", "", text);
  node.htmlFor = target;
  if (required) {
    node.append(" ", element("span", "req", "*"));
  }
  return node;
}

export interface FieldOptions {
  name: string;
  text: string;
  type: string;
  required?: boolean;
  autocomplete?: string;
  placeholder?: string;
}

export function inputField({ name, text, type, required = false, autocomplete = "off", placeholder }: FieldOptions): HTMLDivElement {
  const input = element("input");
  input.type = type;
  input.id = `dpo-app-${name}`;
  input.name = name;
  input.autocomplete = autocomplete as AutoFill;
  input.required = required;
  input.setAttribute("aria-describedby", `dpo-app-${name}-err`);
  if (placeholder) {
    input.placeholder = placeholder;
  }
  if (LIVE_RULES[name]) {
    input.addEventListener("blur", () => {
      liveCheck(input);
    });
    input.addEventListener("input", () => {
      if (input.hasAttribute("aria-invalid")) {
        liveCheck(input);
      }
    });
  }
  const wrapper = element("div", "dpo-app-field");
  wrapper.append(label(input.id, text, required), input, errorBox(name));
  return wrapper;
}

export function selectField(id: string, name: string, text: string, options: [string, string][]): { wrapper: HTMLDivElement; select: HTMLSelectElement } {
  const select = element("select");
  select.id = id;
  select.name = name;
  options.forEach(([value, caption]) => {
    const option = element("option", "", caption);
    option.value = value;
    select.appendChild(option);
  });
  const wrapper = element("div", "dpo-app-field");
  wrapper.append(label(id, text, false), select);
  return { wrapper, select };
}

export function row(...children: HTMLElement[]): HTMLDivElement {
  const node = element("div", "dpo-app-row");
  node.append(...children);
  return node;
}
