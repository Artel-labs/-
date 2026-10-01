import { EMAIL_TYPO, emailLooksValid, phoneProblem } from "../form-rules.ts";

export const START_PARAM_MAX = 512;
const START_PARAM_SHAPE = /^[A-Za-z0-9_-]+$/;
const PROGRAM_PART = /^p_([A-Za-z0-9_]{1,40})$/;
const CAMPAIGN_PART = /^c_([A-Za-z0-9_]{1,64})$/;
const NBSP = " ";

export const LIMITS = { firstName: 80, lastName: 80, phone: 40, email: 160, position: 120, company: 160 } as const;

export type FieldName = keyof typeof LIMITS;
export type Values = Record<FieldName, string>;

export interface ApplicationDraft extends Values {
  consent: boolean;
}

export interface FieldError {
  field: FieldName | "consent";
  message: string;
}

export type Validation = { ok: true; values: Values } | { ok: false; errors: FieldError[] };

export interface StartParam {
  programId: string | null;
  campaign: string | null;
}

export function parseStartParam(raw: string | null | undefined, knownIds: string[]): StartParam {
  const out: StartParam = { programId: null, campaign: null };
  if (typeof raw !== "string" || !raw || raw.length > START_PARAM_MAX || !START_PARAM_SHAPE.test(raw)) {
    return out;
  }
  raw.split("-").forEach((part) => {
    const program = PROGRAM_PART.exec(part)?.[1];
    if (program && out.programId === null && knownIds.includes(program)) {
      out.programId = program;
      return;
    }
    const campaign = CAMPAIGN_PART.exec(part)?.[1];
    if (campaign && out.campaign === null) {
      out.campaign = campaign;
    }
  });
  return out;
}

function clean(value: string, limit: number): string {
  return value.replace(/\s+/g, " ").trim().slice(0, limit);
}

function cleaned(draft: ApplicationDraft): Values {
  return Object.fromEntries((Object.keys(LIMITS) as FieldName[]).map((name) => [name, clean(draft[name], LIMITS[name])])) as Values;
}

function phoneError(phone: string): string {
  return phone ? phoneProblem(phone) : "Укажите телефон.";
}

function emailError(email: string): string {
  if (!email) {
    return "Укажите электронную почту.";
  }
  return emailLooksValid(email) ? "" : EMAIL_TYPO;
}

export function validateApplication(draft: ApplicationDraft): Validation {
  const values = cleaned(draft);
  const checks: [FieldError["field"], string][] = [
    ["firstName", values.firstName ? "" : "Укажите имя."],
    ["lastName", values.lastName ? "" : "Укажите фамилию."],
    ["phone", phoneError(values.phone)],
    ["email", emailError(values.email)],
    ["consent", draft.consent ? "" : "Без согласия на обработку персональных данных заявку принять нельзя."],
  ];
  const errors = checks.filter(([, message]) => message).map(([field, message]) => ({ field, message }));
  return errors.length ? { ok: false, errors } : { ok: true, values };
}

export function filterPrograms<T extends { sphere: string | null; title: string; tagline: string }>(programs: T[], sphere: string, query: string): T[] {
  const needle = query.trim().toLowerCase();
  return programs.filter((program) => {
    if (sphere && sphere !== "all" && program.sphere !== sphere) {
      return false;
    }
    return !needle || `${program.title} ${program.tagline}`.toLowerCase().includes(needle);
  });
}

export function formatPrice(amount: number | null): string {
  if (typeof amount !== "number" || !Number.isFinite(amount) || amount <= 0) {
    return "";
  }
  return `${String(Math.round(amount)).replace(/\B(?=(\d{3})+(?!\d))/g, NBSP)}${NBSP}₽`;
}
