export const ENDPOINT = "/api/applications";
export const PROGRAMS_ENDPOINT = "/api/catalog/program-options";
export const CATALOG_URL = "/catalog";
export const FALLBACK_PHONE = "+7 (495) 772-95-90";
export const PROGRAM_TOPIC = "program";
export const CORPORATE = "corporate";
export const PERSONAL = "personal";
export const OTHER_SOURCE = "other";
export const OTHER_PROGRAMS = "Другие программы";
export const OK_STATUS = 200;
export const VALIDATION_STATUS = 400;
export const TOO_MANY_STATUS = 429;
export const SUBMIT_LABEL = "Отправить заявку";
export const SENDING_LABEL = "Отправляем…";
export const VIBRATION_MS = 10;

export const TOPICS: [string, string][] = [
  ["program", "Заявка на программу"],
  ["course-idea", "Идея курса"],
  ["teaching", "Хочу стать преподавателем"],
  ["feedback", "Отзыв о работе центра"],
];

export const TOPIC_TITLES: Record<string, string> = {
  program: "Заявка на обучение",
  "course-idea": "Идея курса",
  teaching: "Стать нашим преподавателем",
  feedback: "Помогите нам стать лучше",
};

export const TOPIC_HINTS: Record<string, string> = {
  "course-idea": "Расскажите в комментарии, какой программы вам не хватает.",
  teaching: "Расскажите в комментарии о себе и о курсе, который готовы вести.",
  feedback: "Поделитесь в комментарии, что стоит улучшить в работе центра или на сайте.",
};

export const SOURCES: [string, string][] = [
  ["hse-site", "Сайт НИУ ВШЭ"],
  ["telegram", "Телеграм-канал"],
  ["search", "Поисковые системы"],
  ["ad", "Реклама или баннер"],
  ["social", "Социальные сети"],
  ["mailing", "Почтовая рассылка"],
  ["board", "Стенд объявлений"],
  ["recommendation", "По рекомендации"],
  ["other", "Другое"],
];
