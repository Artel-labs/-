import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const COMPONENTS = new URL("../components/", import.meta.url);

function visibleText(component: string): string {
  return readFileSync(new URL(component, COMPONENTS), "utf8")
    .replace(/&nbsp;/g, " ")
    .replace(/\s+/g, " ");
}

test("about section keeps the paragraph without the employers sentence", () => {
  const text = visibleText("landing/AboutSection.astro");
  assert.doesNotMatch(text, /охотятся работодатели/);
  assert.match(text, /Наши выпускники — высокооплачиваемые специалисты/);
  assert.match(text, /государственных структурах\.<\/p>/);
});
