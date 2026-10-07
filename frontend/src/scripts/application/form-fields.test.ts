import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { ADS_CHECK, ADS_CONSENT_URL, ANONYMOUS_TOPICS, CONSENT_CHECK, CONSENT_URL } from "./constants.ts";

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
  assert.match(form, /personal\(adsConsentField\(\)\)/);
  assert.match(form, /\[personal\(label\), personal\(errorBox\("consent"\)\)\]/);
  assert.match(source("index.ts"), /ANONYMOUS_TOPICS\.includes\(topic\)/);
});

test("comment field warns against special categories of data", () => {
  const form = source("form.ts");
  assert.match(form, /element\("p", "dpo-app-hint", SENSITIVE_HINT\)/);
  assert.match(form, /aria-describedby", "dpo-app-comment-note /);
  assert.match(source("constants.ts"), /SENSITIVE_HINT = "Не\\u00a0указывайте сведения о\\u00a0здоровье/);
});

test("consent checkbox repeats the HSE survey wording word for word", () => {
  assert.equal(
    Object.values(CONSENT_CHECK).join(""),
    "Я подтверждаю, что лично ознакомился с Положением об обработке персональных данных НИУ ВШЭ, вправе предоставлять свои персональные данные и давать согласие на их обработку.",
  );
  assert.equal(CONSENT_URL, "/consent");
  const form = source("form.ts");
  assert.match(form, /newTabLink\(CONSENT_CHECK\.regulation, PRIVACY_POLICY_URL\)/);
  assert.match(form, /newTabLink\(CONSENT_CHECK\.consent, CONSENT_URL\)/);
  assert.doesNotMatch(form, /input\.checked = true/);
});

test("advertising consent is a separate unticked box with the HSE wording", () => {
  assert.equal(Object.values(ADS_CHECK).join(""), "Я выражаю Согласие на получение рассылок информационного и рекламного содержания");
  assert.equal(ADS_CONSENT_URL, "/ads-consent");
  const form = source("form.ts");
  assert.match(form, /newTabLink\(ADS_CHECK\.consent, ADS_CONSENT_URL\)/);
  assert.doesNotMatch(form, /noAnnouncements|Не присылать анонсы|checked = true/);
  assert.match(source("submit.ts"), /adsConsent: data\.has\("adsConsent"\)/);
});
