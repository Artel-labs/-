import { FALLBACK_PHONE, ENDPOINT, OK_STATUS, SENDING_LABEL, SUBMIT_LABEL, TOO_MANY_STATUS, VALIDATION_STATUS } from "./constants";
import { markInvalid } from "./fields";

export interface ChosenProgram {
  id: string;
  title: string;
  url: string;
}

interface FieldError {
  field: string;
  message: string;
}

interface Reply {
  status: number;
  fields: FieldError[];
}

const CHECK_FIELDS = "Проверьте отмеченные поля.";
const TOO_MANY = "Слишком много попыток подряд. Подождите минуту и отправьте ещё раз.";
const FAILED = `Не\u00a0удалось отправить заявку. Попробуйте ещё раз или позвоните: ${FALLBACK_PHONE}`;
const OFFLINE = `Заявка не\u00a0отправлена\u00a0— нет связи с\u00a0сервером. Попробуйте ещё раз или позвоните: ${FALLBACK_PHONE}`;

function text(data: FormData, name: string): string {
  const value = data.get(name);
  return typeof value === "string" ? value : "";
}

export function collect(form: HTMLFormElement, program: ChosenProgram): Record<string, unknown> {
  const data = new FormData(form);
  return {
    topic: text(data, "topic") || "program",
    applicantType: text(data, "applicantType") || "personal",
    employeesCount: text(data, "employeesCount"),
    timeframe: text(data, "timeframe"),
    firstName: text(data, "firstName"),
    lastName: text(data, "lastName"),
    phone: text(data, "phone"),
    email: text(data, "email"),
    company: text(data, "company"),
    comment: text(data, "comment"),
    noAnnouncements: data.has("noAnnouncements"),
    consent: data.has("consent"),
    website: text(data, "website"),
    programId: program.id,
    programTitle: program.title,
    programUrl: program.url,
  };
}

async function send(payload: Record<string, unknown>): Promise<Reply> {
  const response = await fetch(ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = (await response.json().catch(() => ({}))) as { fields?: FieldError[] };
  return { status: response.status, fields: body.fields ?? [] };
}

function clearErrors(form: HTMLFormElement): void {
  form.querySelectorAll(".dpo-app-err").forEach((box) => {
    box.textContent = "";
  });
  form.querySelectorAll("[aria-invalid]").forEach((node) => {
    node.removeAttribute("aria-invalid");
  });
}

function showErrors(form: HTMLFormElement, fields: FieldError[]): void {
  fields.forEach(({ field, message }) => {
    const box = form.querySelector(`#dpo-app-${field}-err`);
    const input = form.querySelector<HTMLElement>(`#dpo-app-${field}`);
    if (box) {
      box.textContent = message;
    }
    if (input) {
      markInvalid(input, message);
    }
  });
  form.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus();
}

function failure(reply: Reply): string {
  if (reply.status === 0) {
    return OFFLINE;
  }
  if (reply.status === VALIDATION_STATUS && reply.fields.length) {
    return CHECK_FIELDS;
  }
  return reply.status === TOO_MANY_STATUS ? TOO_MANY : FAILED;
}

export interface SubmitHandlers {
  onDone: () => void;
  onFailed: (status: number, invalidFields: boolean) => void;
}

export async function submit(form: HTMLFormElement, program: ChosenProgram, { onDone, onFailed }: SubmitHandlers): Promise<void> {
  const button = form.querySelector<HTMLButtonElement>(".dpo-app-submit");
  const status = form.querySelector(".dpo-app-status");
  if (!button || !status) {
    return;
  }
  clearErrors(form);
  status.textContent = "";
  status.classList.remove("is-error");
  button.disabled = true;
  button.textContent = SENDING_LABEL;
  let reply: Reply;
  try {
    reply = await send(collect(form, program));
  } catch {
    reply = { status: 0, fields: [] };
  }
  if (reply.status === OK_STATUS) {
    onDone();
    return;
  }
  button.disabled = false;
  button.textContent = SUBMIT_LABEL;
  const invalidFields = reply.status === VALIDATION_STATUS && reply.fields.length > 0;
  if (invalidFields) {
    showErrors(form, reply.fields);
  }
  status.classList.add("is-error");
  status.textContent = failure(reply);
  onFailed(reply.status, invalidFields);
}
