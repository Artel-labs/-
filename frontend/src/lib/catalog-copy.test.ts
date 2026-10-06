import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { CATALOG_TITLE } from "./catalog-meta.ts";

const SOURCES = new URL("../", import.meta.url);

function visibleText(source: string): string {
  return readFileSync(new URL(source, SOURCES), "utf8")
    .replace(/&nbsp;|\u00a0/g, " ")
    .replace(/\s+/g, " ");
}

const CATALOG_SOURCES = ["components/catalog/CatalogHero.astro", "components/catalog/CatalogHead.astro", "pages/catalog.astro"];

test("catalog title covers both programme kinds without naming lawyers", () => {
  assert.equal(CATALOG_TITLE, "Курсы повышения квалификации и переподготовки · ДПО НИУ ВШЭ");
});

test("catalog heading, list heading and descriptions drop the lawyers audience", () => {
  assert.match(visibleText("components/catalog/CatalogHero.astro"), /<h1>Курсы повышения квалификации и переподготовки<\/h1>/);
  assert.match(visibleText("pages/catalog.astro"), /профессиональной переподготовки<\/h2>/);
  assert.match(visibleText("components/catalog/CatalogHead.astro"), /"Программы повышения квалификации и переподготовки НИУ ВШЭ\."/);
  for (const source of CATALOG_SOURCES) {
    assert.doesNotMatch(visibleText(source).replace(/const KEYWORDS =[^;]*;/, ""), /для юристов/, source);
  }
});

test("catalog keywords still name lawyers for search", () => {
  assert.match(visibleText("components/catalog/CatalogHead.astro"), /курсы для юристов/);
});

test("catalog hero keeps two lead paragraphs without the summit phrase and the browsing hint", () => {
  const text = visibleText("components/catalog/CatalogHero.astro");
  assert.match(text, /<p class="hero-gap">Образование, которое выводит на новый уровень\.<\/p>/);
  assert.match(text, /<p> В каталоге — все программы/);
  assert.doesNotMatch(text, /вершинам юридической практики/);
  assert.doesNotMatch(text, /Выбирайте по направлениям/);
});

test("catalog has no PK/PP legend under the filters", () => {
  assert.doesNotMatch(visibleText("pages/catalog.astro"), /tag-legend|ПК — повышение квалификации/);
  assert.doesNotMatch(visibleText("styles/catalog.css"), /tag-legend/);
});

test("compare table lists teacher names instead of their count", () => {
  const text = visibleText("scripts/compare.ts");
  assert.match(text, /\{ label: "Преподаватели", value: attribute\("data-cmp-teachers"\), list: true \}/);
  assert.doesNotMatch(text, /"Преподавателей"/);
});

test("program counts come from the server label with agreement", () => {
  assert.match(visibleText("components/catalog/Toolbar.astro"), /data-total-label=\{totalLabel\}>\{totalLabel\}</);
  assert.match(visibleText("pages/catalog.astro"), /<Toolbar totalLabel=\{catalog\.total_label\} \/>/);
  const filters = visibleText("scripts/catalog-filters.ts");
  assert.match(filters, /elements\.count\.dataset\.totalLabel/);
  assert.doesNotMatch(filters, /\} программ`/);
});

test("catalog descriptions take the number of programmes from the data", () => {
  const page = visibleText("pages/catalog.astro");
  const head = visibleText("components/catalog/CatalogHead.astro");
  assert.match(page, /НИУ ВШЭ: \$\{catalog\.total_label\} повышения квалификации/);
  assert.match(head, /`\$\{catalog\.total_label\} повышения квалификации/);
  for (const text of [page, head]) {
    assert.doesNotMatch(text, /26 курсов/);
  }
});

test("starts board is a vertical timeline grouped by month", () => {
  const board = visibleText("components/catalog/StartsBoard.astro");
  assert.match(board, /<section class="vt-month" id=\{month\.anchor\}/);
  assert.match(board, /<li class=\{`vt-item vt-\$\{item\.side\}`\}>/);
  assert.match(board, /data-target=\{month\.anchor\}/);
  assert.doesNotMatch(board, /tl-wrap|tl-axis|tl-tick|data-left|placeTimeline/);
  const css = visibleText("styles/catalog.css");
  assert.doesNotMatch(css, /\.tl-wrap|\.tl-up1|\.tl-down1|is-placed/);
  assert.match(css, /\.vt-item \+ \.vt-item\{ margin-top: calc\(var\(--vt-step\) - var\(--vt-card-h\)\); \}/);
});
