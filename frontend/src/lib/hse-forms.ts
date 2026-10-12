export const HSE_WIDGET_BASE = "https://www.hse.ru/n/exp/widgets/widgetPassExpressPoll";
export const HSE_POLL_PAGE_BASE = "https://pravo.hse.ru/dpo/polls";
export const FORM_PAGE_BASE = "/hse-form";
export const FORM_MESSAGE = "dpo-hse-form";
const FORM_ID = /^\d{5,12}$/;
export const CENTER_EMAIL = { user: "dpo-pravo", domain: "hse.ru" } as const;
export const PROGRAM_TOPIC = "program";
export const CORPORATE = "corporate";
export const CORPORATE_SUBJECT = "Корпоративное обучение";
export const PROGRAM_TITLE = "Заявка на обучение";
export const CHOOSER_TITLE = "Выберите программу";

export interface TopicForm {
  title: string;
  form: number;
}

export const TOPIC_FORMS: Readonly<Record<string, TopicForm>> = {
  "course-idea": { title: "Идея для курса", form: 1208796428 },
  feedback: { title: "Что улучшить в курсах", form: 1208796510 },
  teaching: { title: "Стать преподавателем наших курсов", form: 1208796725 },
};

export interface ProgramChoice {
  id: string;
  title: string;
  url: string;
  sphere: string;
  form: number | null;
  hse_url: string;
}

export interface ApplicationRequest {
  topic: string;
  kind: string;
  programId: string;
}

export type Route =
  | { kind: "mail"; href: string }
  | { kind: "form"; title: string; caption: string; form: number; fallback: string }
  | { kind: "hse"; title: string; caption: string; href: string }
  | { kind: "choose" };

export function widgetSrc(form: number): string {
  return `${HSE_WIDGET_BASE}/${String(form)}.js`;
}

export function formPage(form: number): string {
  return `${FORM_PAGE_BASE}/${String(form)}`;
}

export function isFormId(text: string): boolean {
  return FORM_ID.test(text);
}

export function pollPage(form: number): string {
  return `${HSE_POLL_PAGE_BASE}/${String(form)}.html`;
}

export function centerMailto(subject: string): string {
  return `mailto:${CENTER_EMAIL.user}@${CENTER_EMAIL.domain}?subject=${encodeURIComponent(subject)}`;
}

export function needsPrograms(request: ApplicationRequest): boolean {
  return request.kind !== CORPORATE && !TOPIC_FORMS[request.topic];
}

function programRoute(program: ProgramChoice | undefined): Route {
  if (program?.form) {
    return { kind: "form", title: PROGRAM_TITLE, caption: program.title, form: program.form, fallback: program.hse_url || pollPage(program.form) };
  }
  if (program?.hse_url) {
    return { kind: "hse", title: PROGRAM_TITLE, caption: program.title, href: program.hse_url };
  }
  return { kind: "choose" };
}

export function routeFor(request: ApplicationRequest, programs: readonly ProgramChoice[]): Route {
  if (request.kind === CORPORATE) {
    return { kind: "mail", href: centerMailto(CORPORATE_SUBJECT) };
  }
  const topic = TOPIC_FORMS[request.topic];
  if (topic) {
    return { kind: "form", title: topic.title, caption: "", form: topic.form, fallback: pollPage(topic.form) };
  }
  if (!request.programId) {
    return { kind: "choose" };
  }
  return programRoute(programs.find((program) => program.id === request.programId));
}

function normalized(text: string): string {
  return text.replace(/\u00a0/g, " ").toLocaleLowerCase("ru").trim();
}

export function matchPrograms(programs: readonly ProgramChoice[], query: string): ProgramChoice[] {
  const needle = normalized(query);
  return needle ? programs.filter((program) => normalized(program.title).includes(needle)) : [...programs];
}
