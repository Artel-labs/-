import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { PRIVACY_POLICY_URL } from "./brand.ts";

const SOURCES = new URL("../", import.meta.url);

const LINK_SOURCES = [
  "components/SiteFooter.astro",
  "components/CookieBanner.astro",
  "components/document/DocumentFooter.astro",
  "components/landing/LandingFooter.astro",
  "pages/404.astro",
  "scripts/application/form.ts",
  "scripts/tg/form-screen.ts",
];

function source(path: string): string {
  return readFileSync(new URL(path, SOURCES), "utf8");
}

test("privacy policy points to the HSE regulation", () => {
  assert.equal(PRIVACY_POLICY_URL, "https://www.hse.ru/data_protection_regulation");
});

test("every privacy link uses the HSE regulation instead of the local page", () => {
  for (const path of LINK_SOURCES) {
    const text = source(path);
    assert.match(text, /PRIVACY_POLICY_URL/, path);
    assert.doesNotMatch(text, /["']\/privacy["']/, path);
  }
});

test("bot privacy answer links to the HSE regulation", () => {
  const faq = JSON.parse(source("data/bot-faq.json")) as { answers: { id: string; anchor: string }[] };
  const privacy = faq.answers.find((answer) => answer.id === "privacy");
  assert.equal(privacy?.anchor, PRIVACY_POLICY_URL);
  assert.doesNotMatch(source("data/bot-faq.json"), /"\/privacy"/);
});
