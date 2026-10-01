import assert from "node:assert/strict";
import { test } from "node:test";

import { catalogPrograms } from "./fixtures.ts";
import { parseQuery, sameStem, search, stem, type SearchProgram } from "./match.ts";

const PROGRAMS: SearchProgram[] = [
  { id: "1", title: "Актуальные вопросы налогового администрирования", sphere: "Финансовое право", type: "ПК", format: "online", price: 22000, start: "Старт: 5 октября", keywords: ["Налоговые споры", "Юристы"] },
  { id: "2", title: "Английское контрактное право", sphere: "Международное право", type: "ПК", format: "offline", price: 60000, start: null, keywords: ["Договорная работа", "Юристы"] },
  { id: "3", title: "Банкротство юридических лиц", sphere: "Корпоративное и договорное право", type: "ПП", format: "mixed", price: 45000, start: "Старт: 1 ноября", keywords: ["Несостоятельность", "Предприниматели"] },
];
const ids = (programs: SearchProgram[]): string[] => programs.map((program) => program.id);

test("основа слова сводит словоформы к одной", () => {
  const base = stem("налоги");
  assert.equal(stem("налоговый").startsWith(base) || base.startsWith(stem("налоговый")), true);
  assert.equal(stem("налогообложение").startsWith(base), true);
  assert.notEqual(stem("право"), stem("практика"));
});

test("слово из названия и из ключевых слов находит программу", () => {
  assert.deepEqual(search("банкротство", PROGRAMS), { reason: "title", programs: [PROGRAMS[2]] });
  assert.deepEqual(search("несостоятельность", PROGRAMS), { reason: "keywords", programs: [PROGRAMS[2]] });
});

test("цена и формат читаются как ограничение", () => {
  const parsed = parseQuery("онлайн дешевле 30 тысяч");
  assert.equal(parsed.priceMax, 30000);
  assert.equal(parsed.format, "online");
  const out = search("онлайн дешевле 30 тысяч", PROGRAMS);
  assert.equal(out.reason, "filter");
  assert.deepEqual(ids(out.programs), ["1"]);
});

test("пустой запрос и несуществующее слово", () => {
  assert.deepEqual(search("   ", PROGRAMS), { reason: "empty", programs: [] });
  const out = search("криптовалюта", PROGRAMS);
  assert.equal(out.reason, "none");
  assert.deepEqual(ids(out.programs), ["1", "3", "2"]);
});

test("совпадение в названии выше совпадения в ключевых словах", () => {
  assert.equal(search("юристы налоговых", PROGRAMS).programs[0]?.id, "1");
  const programs: SearchProgram[] = [
    { id: "a", title: "Налоговые споры", keywords: [] },
    { id: "b", title: "Общий курс", keywords: ["Налоговое администрирование", "Право"] },
  ];
  assert.equal(search("налоговое право", programs).programs[0]?.id, "a");
});

test("границы цены", () => {
  assert.deepEqual([parseQuery("не дороже 40000").priceMax, parseQuery("не дороже 40000").priceMin], [40000, null]);
  assert.deepEqual(ids(search("не дороже 40000", PROGRAMS).programs), ["1"]);
  assert.equal(parseQuery("за 100000").priceMax, 100000);
  assert.notEqual(search("за 100000", PROGRAMS).reason, "empty");
  assert.equal(search("дешевле 100 тысяч космонавтика", PROGRAMS).reason, "filter");
});

test("основы слов не путаются, а словоформы находят программу", () => {
  assert.notEqual(stem("право"), stem("правка"));
  assert.equal(search("правка документа", [{ id: "x", title: "Международное право", keywords: [] }]).reason, "none");
  for (const form of ["право", "права", "правом", "праву", "правами"]) {
    assert.deepEqual(ids(search(form, [{ id: "p", title: "Международное право", keywords: [] }]).programs), ["p"], form);
  }
  assert.equal(search("право", [{ id: "p", title: "Правовое регулирование цифровой экономики", keywords: [] }]).reason, "title");
  assert.equal(search("суд", [{ id: "s", title: "Морское право: страхование судна", keywords: [] }]).reason, "none");
});

test("слово формата не считается темой", () => {
  const online: SearchProgram[] = [
    { id: "a", title: "Курс права", format: "online", keywords: [] },
    { id: "b", title: "Курс права", format: "online", keywords: ["онлайн-архив записей курса"] },
  ];
  assert.deepEqual(search("онлайн", online), { reason: "filter", programs: online });
  const mixed = online.map((program) => ({ ...program, format: "mixed" }));
  assert.equal(search("смешанный формат", mixed).reason, "filter");
});

test("пп и пк распознаются только отдельным словом", () => {
  assert.equal(parseQuery("пп").type, "ПП");
  assert.equal(parseQuery("хочу пп по праву").type, "ПП");
  assert.equal(parseQuery("нужна пк по финансам").type, "ПК");
  assert.equal(parseQuery("группа поддержки").type, null);
  assert.equal(parseQuery("играю на скрипке").type, null);
  assert.deepEqual(ids(search("пп", [{ id: "pp", title: "Курс", type: "ПП", keywords: [] }, { id: "pk", title: "Курс", type: "ПК", keywords: [] }]).programs), ["pp"]);
});

test("срок не путается с ценой, число не съедает следующее слово", () => {
  assert.equal(parseQuery("программа за 3 месяца").priceMax, null);
  assert.equal(parseQuery("до 3 месяцев").priceMax, null);
  assert.equal(parseQuery("до 30").priceMax, null);
  assert.equal(parseQuery("до 30000").priceMax, 30000);
  assert.equal(parseQuery("до 500 рублей").priceMax, 500);
  assert.equal(parseQuery("до 5 лет").priceMax, null);
  assert.deepEqual(parseQuery("до 5000 летний интенсив").stems, [stem("летний"), stem("интенсив")]);
  assert.deepEqual(parseQuery("до 100000 банкротство").stems, [stem("банкротство")]);
  assert.equal(parseQuery("до 50000 онлайн").format, "online");
  assert.equal(parseQuery("до 50000 пп").type, "ПП");
  assert.deepEqual(parseQuery("виза 5000"), { stems: [stem("виза")], priceMax: null, priceMin: null, format: null, type: null });
});

test("общие слова не дают очков сами по себе", () => {
  assert.equal(sameStem(stem("документальный"), stem("документ")), true);
  assert.deepEqual(parseQuery("документальный сериал").stems, [stem("сериал")]);
  const programs: SearchProgram[] = [{ id: "x", title: "Курс без отношения к вопросу", keywords: ["документ об образовании", "следующий набор стартует скоро", "подобрать индивидуальную программу"] }];
  assert.notEqual(search("какой документ выдают", programs).reason, "keywords");
  assert.notEqual(search("ближайшие старты", programs).reason, "keywords");
  assert.equal(search("подобрать программу", programs).reason, "empty");
});

test("без совпадений выдача по дате старта", () => {
  const programs: SearchProgram[] = [
    { id: "late", title: "Курс", keywords: [], start: "Старт: 1 ноября", start_iso: "2026-11-01" },
    { id: "early", title: "Курс", keywords: [], start: "Старт: 5 октября", start_iso: "2026-10-05" },
    { id: "none", title: "Курс", keywords: [] },
  ];
  assert.deepEqual(ids(search("несуществующее слово чепуха", programs).programs), ["early", "late", "none"]);
});

test("на настоящем каталоге подсказки и темы ведут себя осмысленно", () => {
  const programs = catalogPrograms();
  const onlineCount = programs.filter((program) => program.format === "online").length;
  const online = search("Онлайн", programs);
  assert.equal(online.reason, "filter");
  assert.equal(online.programs.length, onlineCount);
  assert.ok(!["title", "keywords"].includes(search("Сколько стоит", programs).reason));
  assert.ok(["none", "empty"].includes(search("Какой документ выдают", programs).reason));
  assert.ok(["none", "empty"].includes(search("Ближайшие старты", programs).reason));
  assert.equal(search("Подобрать программу", programs).reason, "empty");
  for (const word of ["налоги", "банкротство", "договор", "права"]) {
    assert.ok(!["none", "empty"].includes(search(word, programs).reason), word);
  }
  const bankrupt = search("до 100000 банкротство", programs);
  assert.equal(bankrupt.reason, "title");
  assert.ok(bankrupt.programs[0]?.title.toLowerCase().includes("банкротств"));
  assert.equal(search("за 100000 налоги", programs).reason, "title");
  assert.ok(search("до 50000 онлайн", programs).programs.every((program) => program.format === "online" && (program.price ?? Infinity) <= 50000));
  assert.ok(search("до 200000 пп", programs).programs.every((program) => program.type === "ПП" && (program.price ?? Infinity) <= 200000));
});
