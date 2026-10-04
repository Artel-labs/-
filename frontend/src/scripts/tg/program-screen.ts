import type { TgNotice, TgProgram } from "../../lib/tg";
import type { Bridge } from "./bridge";
import type { Context } from "./context";
import { formatPrice } from "./core.ts";
import { clamped, h, hostOf, icon, list, outLink, picture, plural, section } from "./dom";

const SOURCE_NOTE = "С официальной страницы программы на hse.ru";
const ABOUT_LIMIT = 320;
const TEACHER_LIMIT = 110;

function noticeBlock(bridge: Bridge, notice: TgNotice | null): HTMLElement | null {
  if (!notice) {
    return null;
  }
  return h("div", { class: "notice", role: "note" }, [
    h("p", { class: "notice-head" }, [h("span", { class: "notice-tag", text: "Важно" }), notice.date]),
    h("p", { class: "notice-text", text: notice.text }),
    notice.url ? outLink(bridge, "notice-link", notice.url, [`Смотреть на\u00a0${hostOf(notice.url) || "сайте"} `, icon("arrow-up-right")]) : null,
  ]);
}

function priceBlock(program: TgProgram, price: string): HTMLElement | null {
  if (!price && !program.price_terms.length) {
    return null;
  }
  return h("div", { class: "price-box" }, [
    price ? h("span", { class: "price", text: price }) : null,
    program.old_price ? h("s", { class: "price-old", text: formatPrice(program.old_price) }) : null,
    list("price-terms", program.price_terms, "ul", "check"),
  ]);
}

function modulesBlock(program: TgProgram): HTMLElement | null {
  if (!program.modules.length) {
    return null;
  }
  const sub = plural(program.modules.length, "модуль", "модуля", "модулей") + (program.hours ? ` · ${program.hours}` : "");
  const items = program.modules.map((module) => {
    const head = [h("span", { class: "module-title", text: module.title }), module.hours ? h("span", { class: "module-hours", text: module.hours }) : null];
    if (!module.topics.length) {
      return h("li", null, [h("div", { class: "module-row" }, head)]);
    }
    return h("li", null, [h("details", null, [h("summary", { class: "module-row" }, head), list("module-topics", module.topics)])]);
  });
  return section("Программа обучения", sub, h("ol", { class: "modules" }, items));
}

function filesBlock(bridge: Bridge, program: TgProgram): HTMLElement | null {
  if (!program.files.length) {
    return null;
  }
  const items = program.files.map((file) =>
    h("li", null, [
      outLink(bridge, "file", file.path, [
        h("span", { class: "file-icon", "aria-hidden": "true", text: "PDF" }),
        h("span", { class: "file-name" }, [file.title, h("small", { text: file.size ? `PDF · ${file.size}` : "PDF" })]),
        h("span", { class: "file-go", "aria-hidden": "true" }, [icon("arrow-up-right")]),
      ]),
    ]),
  );
  return section("Документы программы", null, h("ul", { class: "files" }, items));
}

function teachersBlock(bridge: Bridge, program: TgProgram): HTMLElement | null {
  if (!program.teachers.length) {
    return null;
  }
  const title = program.teachers.length === 1 ? "Преподаватель-практик" : "Преподаватели-практики";
  const items = program.teachers.map((teacher) =>
    h("li", { class: "teacher" }, [
      teacher.photo
        ? h("img", { class: "teacher-photo", src: teacher.photo, alt: "", loading: "lazy", decoding: "async" })
        : h("span", { class: "teacher-photo", "aria-hidden": "true" }),
      h("div", null, [
        teacher.page
          ? h("p", { class: "teacher-name" }, [outLink(bridge, null, teacher.page, [`${teacher.name} `, icon("arrow-up-right")])])
          : h("p", { class: "teacher-name", text: teacher.name }),
        teacher.about ? clamped("teacher-about", teacher.about, TEACHER_LIMIT) : null,
      ]),
    ]),
  );
  return section(title, null, h("ul", { class: "teachers" }, items));
}

function feedbackBlock(program: TgProgram): HTMLElement | null {
  if (!program.feedback.length) {
    return null;
  }
  const reviews = h(
    "ul",
    { class: "reviews" },
    program.feedback.map((item) => h("li", null, [h("blockquote", { text: item.text }), item.author ? h("p", { class: "review-author", text: item.author }) : null])),
  );
  return section("Отзывы выпускников", SOURCE_NOTE, h("div", { class: "reviews-scroll", role: "region", tabindex: "0", "aria-label": "Отзывы, листаются вбок" }, [reviews]));
}

function faqBlock(program: TgProgram): HTMLElement | null {
  if (!program.faq.length) {
    return null;
  }
  const items = program.faq.map((item) => h("li", null, [h("details", null, [h("summary", { text: item.q }), h("p", { class: "faq-a", text: item.a })])]));
  return section("Вопросы и ответы", SOURCE_NOTE, h("ul", { class: "faq" }, items));
}

function aboutBlock(program: TgProgram): HTMLElement | null {
  const text = program.about || program.tagline;
  if (!text) {
    return null;
  }
  const body = program.about_items ? list("bul", program.about_items) : clamped("about", text, ABOUT_LIMIT);
  return section("О программе", null, h("div", null, [program.lead ? h("p", { class: "about-lead", text: program.lead }) : null, body]));
}

function factsBlock(program: TgProgram): HTMLElement | null {
  const facts: [string, string | null][] = [
    ["Старт", program.start_label ? program.start_label.replace(/^Старт:\s*/, "") : null],
    ["Формат", program.format],
    ["Длительность", program.duration],
    ["Объём", program.hours],
    ["Язык", program.language],
    ["График", program.schedule],
    ["Документ", program.doc],
  ];
  const shown = facts.filter((fact): fact is [string, string] => Boolean(fact[1]));
  if (!shown.length) {
    return null;
  }
  return h("dl", { class: "facts" }, shown.map(([label, value]) => h("div", { class: "fact" }, [h("dt", { text: label }), h("dd", { text: value })])));
}

function audience(program: TgProgram): string[] {
  return program.audience.map((item) => item.replace(/[,;.]\s*$/, ""));
}

export function programScreen(context: Context): HTMLElement {
  const program = context.program();
  const price = formatPrice(program.price);
  const { bridge } = context;
  bridge.setMain(price ? `Подать заявку · ${price}` : "Подать заявку", () => {
    context.go("form");
  });
  return h("article", { "aria-label": program.title }, [
    h("div", { class: "hero" }, [picture(program.cover)]),
    h("div", { class: "badges" }, [program.badge && h("span", { class: "badge", text: program.badge }), program.format && h("span", { class: "badge", text: program.format })]),
    h("h1", { class: "h1 h1--sm", text: program.title }),
    noticeBlock(bridge, program.notice),
    factsBlock(program),
    priceBlock(program, price),
    aboutBlock(program),
    section("Кому подойдёт программа", program.audience_intro, list("pills", audience(program))),
    section("Чему вы научитесь", null, list("bul", program.results)),
    section("Преимущества программы", null, list("advantages", program.advantages, "ol")),
    modulesBlock(program),
    filesBlock(bridge, program),
    teachersBlock(bridge, program),
    feedbackBlock(program),
    section("Документы для приёма", null, list("bul", program.admission_docs)),
    faqBlock(program),
  ]);
}
