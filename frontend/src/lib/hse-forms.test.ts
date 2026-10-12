import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";
import {
  CORPORATE,
  PROGRAM_TITLE,
  PROGRAM_TOPIC,
  TOPIC_FORMS,
  centerMailto,
  formPage,
  isFormId,
  matchPrograms,
  needsPrograms,
  pollPage,
  routeFor,
  widgetSrc,
  type ProgramChoice,
} from "./hse-forms.ts";

const SOURCES = new URL("../", import.meta.url);
const ENGLISH: ProgramChoice = {
  id: "856421092",
  title: "Английское контрактное право",
  url: "/programs/angliyskoe.html",
  sphere: "Международное право",
  form: 856420964,
  hse_url: "https://www.hse.ru/edu/dpo/856421092",
};
const NO_FORM: ProgramChoice = { ...ENGLISH, id: "1", title: "Морской арбитраж", form: null, hse_url: "https://www.hse.ru/edu/dpo/1" };
const PROGRAMS = [ENGLISH, NO_FORM];

function source(path: string): string {
  return readFileSync(new URL(path, SOURCES), "utf8");
}

test("topic buttons open the HSE forms the centre made", () => {
  assert.deepEqual(TOPIC_FORMS, {
    "course-idea": { title: "Идея для курса", form: 1208796428 },
    feedback: { title: "Что улучшить в курсах", form: 1208796510 },
    teaching: { title: "Стать преподавателем наших курсов", form: 1208796725 },
  });
  assert.deepEqual(routeFor({ topic: "teaching", kind: "", programId: "" }, []), {
    kind: "form",
    title: "Стать преподавателем наших курсов",
    caption: "",
    form: 1208796725,
    fallback: "https://pravo.hse.ru/dpo/polls/1208796725.html",
  });
});

test("corporate training opens a letter to the centre", () => {
  assert.equal(centerMailto("Корпоративное обучение"), "mailto:dpo-pravo@hse.ru?subject=%D0%9A%D0%BE%D1%80%D0%BF%D0%BE%D1%80%D0%B0%D1%82%D0%B8%D0%B2%D0%BD%D0%BE%D0%B5%20%D0%BE%D0%B1%D1%83%D1%87%D0%B5%D0%BD%D0%B8%D0%B5");
  assert.equal(routeFor({ topic: PROGRAM_TOPIC, kind: CORPORATE, programId: "" }, []).kind, "mail");
  assert.equal(needsPrograms({ topic: PROGRAM_TOPIC, kind: CORPORATE, programId: "" }), false);
});

test("programme button opens the programme's own HSE form", () => {
  assert.deepEqual(routeFor({ topic: PROGRAM_TOPIC, kind: "", programId: ENGLISH.id }, PROGRAMS), {
    kind: "form",
    title: PROGRAM_TITLE,
    caption: ENGLISH.title,
    form: 856420964,
    fallback: ENGLISH.hse_url,
  });
  assert.equal(widgetSrc(856420964), "https://www.hse.ru/n/exp/widgets/widgetPassExpressPoll/856420964.js");
  assert.equal(pollPage(1208796428), "https://pravo.hse.ru/dpo/polls/1208796428.html");
});

test("programme without an HSE form leads to its page on hse.ru", () => {
  assert.deepEqual(routeFor({ topic: PROGRAM_TOPIC, kind: "", programId: NO_FORM.id }, PROGRAMS), {
    kind: "hse",
    title: PROGRAM_TITLE,
    caption: NO_FORM.title,
    href: NO_FORM.hse_url,
  });
});

test("general button and unknown programme ask to choose a programme first", () => {
  assert.deepEqual(routeFor({ topic: PROGRAM_TOPIC, kind: "", programId: "" }, PROGRAMS), { kind: "choose" });
  assert.deepEqual(routeFor({ topic: PROGRAM_TOPIC, kind: "", programId: "404" }, PROGRAMS), { kind: "choose" });
  assert.equal(needsPrograms({ topic: PROGRAM_TOPIC, kind: "", programId: "" }), true);
});

test("programme search ignores case and non-breaking spaces", () => {
  assert.deepEqual(matchPrograms(PROGRAMS, "  КОНТРАКТНОЕ право "), [ENGLISH]);
  assert.deepEqual(matchPrograms(PROGRAMS, ""), PROGRAMS);
});

test("our own application form no longer collects data on the site", () => {
  for (const removed of ["scripts/application/form.ts", "scripts/application/submit.ts", "scripts/application/fields.ts", "scripts/application/done.ts"]) {
    assert.ok(!existsSync(new URL(removed, SOURCES)), removed);
  }
  const scripts = ["index.ts", "chooser.ts", "frame.ts", "programs.ts", "constants.ts"].map((name) => source(`scripts/application/${name}`)).join("\n");
  assert.doesNotMatch(scripts, /\/api\/applications|method: "POST"|FormData/);
});

test("HSE form lives on its own page shown in a frame", () => {
  assert.equal(formPage(856420964), "/hse-form/856420964");
  assert.equal(isFormId("856420964"), true);
  for (const bad of ["", "12", "abc", "856420964.js", "1/2", "1234567890123"]) {
    assert.equal(isFormId(bad), false, bad);
  }
  const page = source("pages/hse-form/[id].astro");
  assert.match(page, /if \(!isFormId\(id\)\) \{\s+return new Response\(null, \{ status: 404 \}\);/);
  assert.match(page, /<script is:inline src=\{src\}><\/script>/);
  assert.match(page, /name="robots" content="noindex, nofollow"/);
  assert.match(source("scripts/application/frame.ts"), /event\.origin !== window\.location\.origin \|\| event\.source !== frame\.contentWindow/);
  const size = source("scripts/hse-form-frame.ts");
  assert.match(size, /height: content\.offsetHeight/);
  assert.match(size, /window\.parent\.postMessage\([^)]*window\.location\.origin\)/);
});

function nginx(name: string): string {
  return readFileSync(new URL(`../../deploy/nginx/snippets/${name}`, SOURCES), "utf8");
}

test("only the form page relaxes the security policy", () => {
  const site = nginx("site-headers.conf");
  assert.doesNotMatch(site, /unsafe-eval|unsafe-inline|hse\.ru|google/);
  const form = nginx("form-headers.conf");
  assert.match(form, /script-src 'self' 'unsafe-eval' https:\/\/www\.hse\.ru\/n\/ https:\/\/www\.google\.com\/recaptcha\/ https:\/\/www\.gstatic\.com\/recaptcha\/;/);
  assert.match(form, /connect-src 'self' https:\/\/www\.hse\.ru\/n\/;/);
  assert.match(form, /frame-ancestors 'self'/);
  assert.match(form, /X-Frame-Options SAMEORIGIN/);
  assert.doesNotMatch(form, /unsafe-inline/);
  const routes = nginx("site.conf");
  assert.match(routes, /location ~ "\^\/hse-form\/\[0-9\]\{5,12\}\$" \{\n[^}]*include \/etc\/nginx\/snippets\/form-headers\.conf;/);
  assert.doesNotMatch(nginx("admin-headers.conf"), /hse\.ru|google/);
});
