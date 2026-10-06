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

test("documents card keeps the link without the academic school paragraph", () => {
  const text = visibleText("landing/AboutSection.astro");
  assert.doesNotMatch(text, /Академическая школа университета/);
  assert.doesNotMatch(text, /разбор кейсов ведут/);
  assert.match(text, /Посмотреть образцы документов/);
});

test("documents card title speaks of a document, not a diploma", () => {
  const text = visibleText("landing/AboutSection.astro");
  assert.match(text, /about-card-title">Документ НИУ ВШЭ, а преподают практикующие юристы</);
  assert.doesNotMatch(text, /Диплом НИУ ВШЭ и преподаватели/);
});

test("hero lead names corporate lawyers instead of in-house counsel", () => {
  const text = visibleText("landing/HeroSection.astro");
  assert.match(text, /практикующих и корпоративных юристов, руководителей правовых департаментов/);
  assert.doesNotMatch(text, /in-house/);
});

test("practitioners card ends with the list of roles", () => {
  const text = visibleText("landing/WhyUsSection.astro");
  assert.match(text, /ординарные профессора и заслуженные деятели науки\.<\/p>/);
  assert.doesNotMatch(text, /формирует правовой ландшафт/);
});

test("documents card in why-us states only who issues the documents", () => {
  const text = visibleText("landing/WhyUsSection.astro");
  assert.match(text, /Все документы об окончании обучения выдаёт непосредственно НИУ ВШЭ\.<\/p>/);
  assert.doesNotMatch(text, /высоко ценятся работодателями/);
});

test("training results block states only who issues the documents", () => {
  const text = visibleText("landing/DocumentSection.astro");
  assert.match(text, /выдаются непосредственно НИУ ВШЭ\. После успешного окончания/);
  assert.doesNotMatch(text, /высоко ценятся работодателями/);
});
