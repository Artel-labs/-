import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { filterPrograms, formatPrice, parseStartParam, START_PARAM_MAX, validateApplication, type ApplicationDraft, type Validation } from "./core.ts";

const IDS = ["494685723", "961021723"];
const NONE = { programId: null, campaign: null };
const CASES = JSON.parse(readFileSync(new URL("./validation-cases.json", import.meta.url), "utf8")) as { input: ApplicationDraft; output: Validation }[];
const NBSP = " ";

test("startapp: программа, метка и оба вместе в любом порядке", () => {
  assert.deepEqual(parseStartParam("p_494685723", IDS), { programId: "494685723", campaign: null });
  assert.deepEqual(parseStartParam("c_yuriy2", IDS), { programId: null, campaign: "yuriy2" });
  assert.deepEqual(parseStartParam("p_494685723-c_yuriy2", IDS), { programId: "494685723", campaign: "yuriy2" });
  assert.deepEqual(parseStartParam("c_yuriy2-p_961021723", IDS), { programId: "961021723", campaign: "yuriy2" });
});

test("startapp: мусор, чужие символы и неизвестный id молча игнорируются", () => {
  for (const raw of [undefined, null, "", "x", "p_", "c_", "q_1", "p_000", "p_494685723 c_a", "c_a b", "c_имя", "p_494685723%2F"]) {
    assert.deepEqual(parseStartParam(raw, IDS), NONE, String(raw));
  }
  assert.deepEqual(parseStartParam(`c_${"a".repeat(65)}`, IDS), NONE);
  assert.deepEqual(parseStartParam(`p_494685723-${"x".repeat(600)}`, IDS), NONE);
  assert.deepEqual(parseStartParam("p_494685723-zz", IDS), { programId: "494685723", campaign: null });
  assert.equal(START_PARAM_MAX, 512);
});

test("проверка заявки совпадает с прежним мини-приложением", () => {
  for (const { input, output } of CASES) {
    assert.deepEqual(validateApplication(input), output, JSON.stringify(input));
  }
});

test("витрина: фильтр по сфере и поиск без учёта регистра", () => {
  const programs = [
    { id: "1", title: "Корпоративное право", tagline: "Сделки", sphere: "corporate" },
    { id: "2", title: "Нейроправо", tagline: "Мозг и суд", sphere: "digital" },
  ];
  const ids = (list: { id: string }[]): string[] => list.map((program) => program.id);
  assert.deepEqual(ids(filterPrograms(programs, "all", "")), ["1", "2"]);
  assert.deepEqual(ids(filterPrograms(programs, "digital", "")), ["2"]);
  assert.deepEqual(ids(filterPrograms(programs, "all", "  СДЕЛКИ ")), ["1"]);
  assert.deepEqual(ids(filterPrograms(programs, "corporate", "мозг")), []);
});

test("витрина: поиск находит название с неразрывными пробелами", () => {
  const programs = [{ id: "1", title: `Право${NBSP}— в${NBSP}семье`, tagline: "", sphere: "practice" }];
  assert.deepEqual(
    filterPrograms(programs, "all", "право — в семье").map((program) => program.id),
    ["1"],
  );
});

test("цена: неразрывные пробелы, пусто без цены", () => {
  assert.equal(formatPrice(390000), `390${NBSP}000${NBSP}₽`);
  assert.equal(formatPrice(null), "");
  assert.equal(formatPrice(0), "");
});
