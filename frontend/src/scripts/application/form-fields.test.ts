import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { ANONYMOUS_TOPICS } from "./constants.ts";

function source(name: string): string {
  return readFileSync(new URL(name, import.meta.url), "utf8");
}

test("application form does not ask for a job title", () => {
  for (const name of ["form.ts", "submit.ts"]) {
    assert.doesNotMatch(source(name), /position|Должность/i, name);
  }
});

test("application form does not ask how the applicant found the centre", () => {
  for (const name of ["form.ts", "submit.ts", "constants.ts"]) {
    assert.doesNotMatch(source(name), /sources|sourceOther|узнали/i, name);
  }
});

test("customer organisation is asked only in the corporate block", () => {
  const form = source("form.ts");
  const corporate = form.slice(form.indexOf("function corporateBlock"), form.indexOf("function programField"));
  assert.match(corporate, /name: "company", text: "Организация-заказчик"/);
  assert.equal(form.match(/name: "company"/g)?.length, 1);
  assert.doesNotMatch(form, /Место работы|dpo-app-more/);
});

test("anonymous topics match the server rules", () => {
  const shared = JSON.parse(readFileSync(new URL("../../../../shared/application-topics.json", import.meta.url), "utf8")) as { anonymous: string[] };
  assert.deepEqual([...ANONYMOUS_TOPICS], shared.anonymous);
});

test("contacts, consent and announcements are hidden for anonymous topics", () => {
  const form = source("form.ts");
  assert.match(form, /personal\(row\(\s*inputField\(\{ name: "lastName"/);
  assert.match(form, /personal\(row\(\s*inputField\(\{ name: "phone"/);
  assert.match(form, /personal\(checkbox\("noAnnouncements"/);
  assert.match(form, /\[personal\(label\), personal\(errorBox\("consent"\)\)\]/);
  assert.match(source("index.ts"), /ANONYMOUS_TOPICS\.includes\(topic\)/);
});
