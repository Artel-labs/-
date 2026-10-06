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

test("top programs block is titled by listeners choice without intro and legend", () => {
  const text = visibleText("landing/TopProgramsSection.astro");
  assert.match(text, /<h2 class="dpo-h2">Выбор слушателей<\/h2>/);
  assert.doesNotMatch(text, /dpo-eyebrow/);
  assert.doesNotMatch(text, /Популярные программы повышения квалификации/);
  assert.doesNotMatch(text, /Право меняется быстрее/);
  assert.doesNotMatch(text, /итог — удостоверение/);
});

test("top program tile shows the start over the cover without rank, price and description", () => {
  const tile = visibleText("landing/TopProgramTile.astro");
  assert.match(tile, /dpo-tile-cover[^>]*>\{program\.start && <span class="dpo-tile-start">/);
  assert.doesNotMatch(tile, /program\.(rank|price|tagline)/);
  assert.match(tile, /Подать заявку/);
});

test("top programs are laid out as a grid, not a carousel", () => {
  const section = visibleText("landing/TopProgramsSection.astro");
  assert.match(section, /class="dpo-top5-grid"/);
  assert.doesNotMatch(section, /data-dpo-scroll/);
});

test("sphere tiles are colored as a checkerboard by position, not by sphere", () => {
  const css = readFileSync(new URL("../styles/landing.css", import.meta.url), "utf8");
  assert.doesNotMatch(css, /\.dpo-sphere\[data-sphere=/);
  assert.match(css, /\.dpo-sphere:nth-child\(odd\) \{ --tile-bg: var\(--sphere-dark-bg\)/);
  assert.match(css, /\.dpo-sphere:nth-child\(4n\+4\) \{ --tile-bg: var\(--sphere-dark-bg\)/);
});

test("teachers intro has no carousel hint and no duplicated cases sentence", () => {
  const teachers = visibleText("landing/TeachersSection.astro");
  assert.doesNotMatch(teachers, /Листайте ленту/);
  assert.doesNotMatch(teachers, /реальные кейсы и актуальная судебная практика/);
  assert.match(visibleText("landing/WhyUsSection.astro"), /реальные кейсы и актуальная судебная практика/);
});

test("teachers intro lists only roles confirmed by teacher cards", () => {
  const teachers = visibleText("landing/TeachersSection.astro");
  assert.match(teachers, /Курсы ведут преподаватели факультета права НИУ ВШЭ вместе с практиками: партнёрами юридических фирм, адвокатами, юристами компаний и судьёй в отставке\./);
  assert.doesNotMatch(teachers, /формирует правовой ландшафт/);
});

test("feedback block is titled by the ideas sentence", () => {
  const explore = visibleText("landing/ExploreSection.astro");
  assert.match(explore, /<h2 class="dpo-h2">Ваш опыт и идеи помогут нам стать ещё лучше<\/h2>/);
  assert.match(explore, /<p class="dpo-lead">Мы постоянно развиваемся и хотим, чтобы наши программы оставались самыми актуальными\.<\/p>/);
  assert.doesNotMatch(explore, /Помогите нам стать лучше/);
});

test("feedback cards use three palette colors and keep them on hover", () => {
  const sections = readFileSync(new URL("../styles/landing-sections.css", import.meta.url), "utf8");
  const landing = readFileSync(new URL("../styles/landing.css", import.meta.url), "utf8");
  assert.match(sections, /\.explore-card-box:nth-child\(3n\+1\) \{ --card-bg: rgb\(var\(--hse-blue\)\)/);
  assert.match(sections, /\.explore-card-box:nth-child\(3n\+2\) \{ --card-bg: rgb\(var\(--hse-blue-2\)\)/);
  assert.match(sections, /\.explore-card-box:nth-child\(3n\+3\) \{ --card-bg: rgb\(var\(--hse-blue-4\)\)/);
  assert.doesNotMatch(landing, /#explore a\.explore-card:hover,[^}]*background:/);
});
