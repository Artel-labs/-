import assert from "node:assert/strict";
import { test } from "node:test";

import { botData, faq } from "./fixtures.ts";
import { ActionQueue } from "./queue.ts";
import { detectIntent, formatPrice, pickBy, priceRange, reply, sphereList, upcoming } from "./reply.ts";

const data = botData();

function kindOf(query: string): string {
  return reply(query, data).kind;
}

function answerOf(query: string): string | undefined {
  const out = reply(query, data);
  return out.kind === "answer" ? out.answer.id : undefined;
}

test("подбор по сферам и типам не пуст", () => {
  const spheres = sphereList(data.programs);
  assert.ok(spheres.length >= 2);
  for (const sphere of spheres) {
    assert.ok(pickBy(data.programs, "sphere", sphere).length > 0, sphere);
  }
  assert.ok(pickBy(data.programs, "type", "ПК").length > 0);
  assert.ok(pickBy(data.programs, "type", "ПП").length > 0);
});

test("подсказки дают осмысленный ответ", () => {
  const online = reply("Онлайн", data);
  assert.equal(online.kind, "programs");
  assert.equal(data.programs.filter((program) => program.format === "online").length, 19);
  assert.equal(answerOf("Какой документ выдают"), "document");
  const starts = upcoming(data.programs, 5).filter((program) => program.start_iso ?? program.start);
  assert.ok(starts.length > 0);
  starts.slice(1).forEach((program, index) => {
    assert.ok((starts[index]?.start_iso ?? "") <= (program.start_iso ?? ""));
  });
  const range = priceRange(data.programs);
  assert.ok(range && range.min > 0 && range.max > range.min);
  assert.equal(formatPrice(22000), "22 000 ₽");
});

test("намерения распознаются по кнопке и по набранному тексту", () => {
  assert.equal(detectIntent("Подобрать программу"), "pickProgram");
  assert.equal(detectIntent("Ближайшие старты"), "upcomingStarts");
  assert.equal(detectIntent("Сколько стоит"), "priceRange");
  assert.equal(detectIntent("цена"), "priceRange");
  assert.equal(detectIntent("когда старт"), "upcomingStarts");
  assert.equal(detectIntent("до 30000"), null);
  assert.equal(detectIntent("Онлайн"), null);
  assert.equal(detectIntent("пк и пп в чём разница"), null);
});

test("готовые ответы и честные пробелы", () => {
  const privacy = reply("персональные данные", data);
  assert.equal(privacy.kind === "answer" && privacy.answer.id, "privacy");
  assert.ok(privacy.kind === "answer" && privacy.extra?.length);
  const difference = reply("пк и пп в чём разница", data);
  assert.equal(difference.kind === "answer" && difference.answer.id, "pk-vs-pp");
  assert.ok(difference.kind === "answer" && !difference.extra);
  assert.equal(answerOf("можно без юридического образования"), "no-legal-background");
  for (const query of ["какие есть скидки", "налоговый вычет", "есть ли скидка для организации"]) {
    assert.equal(answerOf(query), "discounts", query);
  }
  assert.equal(answerOf("какие документы нужны для поступления"), "admission-docs");
  const payment = reply("оплата", data);
  assert.equal(payment.kind === "gap" && payment.gap.id, "payment");
});

test("сильные и слабые совпадения по теме", () => {
  const bankrupt = reply("банкротство", data);
  assert.equal(bankrupt.kind, "programs");
  assert.ok(bankrupt.kind === "programs" && bankrupt.programs.length === 1 && /банкротств/i.test(bankrupt.programs[0]?.title ?? ""));
  const taxes = reply("налоги", data);
  assert.ok(taxes.kind === "programs" && taxes.programs.length === 2 && taxes.programs.every((program) => /налог/i.test(program.title)));
  assert.equal(kindOf("сделка"), "programs-weak");
  const rights = reply("права", data);
  assert.equal(rights.kind === "programs" && rights.intro, "Вот что нашла:");
});

test("очередь действий ждёт данные, отдаёт их всем и помнит отказ", () => {
  const queue = new ActionQueue<{ ok: boolean }>();
  const seen: { ok: boolean }[] = [];
  assert.equal(queue.run((value) => seen.push(value), () => undefined), "queued");
  queue.run((value) => seen.push(value), () => undefined);
  assert.equal(queue.resolve({ ok: true }), 2);
  assert.deepEqual(seen, [{ ok: true }, { ok: true }]);
  assert.equal(queue.run((value) => seen.push(value), () => undefined), "ran");
  const failing = new ActionQueue<number>();
  let failures = 0;
  failing.run(() => assert.fail("не должно вызываться"), () => failures++);
  assert.equal(failing.reject(), 1);
  assert.equal(failing.run(() => assert.fail("не должно вызываться"), () => failures++), "failed");
  assert.equal(failures, 2);
  assert.equal(failing.status(), false);
});

test("база ответов: устойчивые id, якоря на новые адреса, без длинного тире", () => {
  const entries = faq();
  const all = [...entries.answers, ...entries.gaps, entries.duration];
  assert.equal(new Set(all.map((entry) => entry.id)).size, all.length);
  for (const entry of [...entries.answers, entries.duration]) {
    assert.match(entry.anchor, /^\/(catalog|privacy)?(#[\w-]+)?$/, entry.id);
  }
  for (const entry of all) {
    assert.ok(entry.triggers.length > 0 && entry.triggers.every((trigger) => trigger.trim() && !trigger.includes("—")), entry.id);
  }
  assert.ok(entries.answers.every((answer) => !answer.text.includes("—")));
  assert.ok(entries.answers.some((answer) => answer.note && !answer.text.includes(answer.note)));
});
