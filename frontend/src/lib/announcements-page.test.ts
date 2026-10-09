import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";
import { ANNOUNCEMENTS_LINK_LABEL, ANNOUNCEMENTS_PATH } from "./nav.ts";

const SOURCES = new URL("../", import.meta.url);

function visibleText(source: string): string {
  return readFileSync(new URL(source, SOURCES), "utf8")
    .replace(/&nbsp;|\u00a0/g, " ")
    .replace(/\s+/g, " ");
}

test("announcements page has its own address and label", () => {
  assert.equal(ANNOUNCEMENTS_PATH, "/announcements");
  assert.equal(ANNOUNCEMENTS_LINK_LABEL, "Анонсы программ");
  assert.ok(existsSync(new URL("pages/announcements.astro", SOURCES)));
  assert.ok(!existsSync(new URL("components/catalog/StartsBoard.astro", SOURCES)));
});

test("announcements hero names the calendar of starts", () => {
  const hero = visibleText("components/announcements/AnnouncementsHero.astro");
  assert.match(hero, /<span class="eyebrow">Календарь стартов<\/span>/);
  assert.match(hero, /<h1>\{ANNOUNCEMENTS_LINK_LABEL\}<\/h1>/);
  assert.match(hero, /Ближайшие старты программ повышения квалификации и переподготовки — по датам\./);
});

test("announcements page loads the board from the server and answers 404 without data", () => {
  const page = visibleText("pages/announcements.astro");
  assert.match(page, /const page = await fetchAnnouncementsPage\(\);/);
  assert.match(page, /new Response\(null, \{ status: 404 \}\)/);
  assert.match(page, /<AnnouncementsBoard starts=\{page\.starts\} \/>/);
  assert.match(visibleText("lib/announcements.ts"), /fetchOptional<AnnouncementsPage>\("\/catalog\/announcements"\)/);
});

test("announcements board groups cards by month under a vertical line", () => {
  const board = visibleText("components/announcements/AnnouncementsBoard.astro");
  assert.match(board, /<section class="an-month" id=\{month\.anchor\}/);
  assert.match(board, /<h2 class="an-month-label" id=\{`\$\{month\.anchor\}-title`\}> \{month\.caption\} <\/h2>/);
  assert.match(board, /<ol class="an-items">/);
  assert.match(board, /data-target=\{month\.anchor\}/);
  assert.match(board, /<a class="tl-card" href=\{sitePath\(item\.path\)\}/);
  assert.doesNotMatch(board, /item\.side/);
});

test("announcements grid shows one, two and four cards per row", () => {
  const css = visibleText("styles/announcements.css");
  assert.match(css, /\.an-items\{[^}]*grid-template-columns: 1fr;/);
  assert.match(css, /@media \(min-width: 640px\)\{ \.an-items\{ grid-template-columns: repeat\(2, minmax\(0, 1fr\)\); \} \}/);
  assert.match(css, /@media \(min-width: 1200px\)\{ \.an-items\{ grid-template-columns: repeat\(4, minmax\(0, 1fr\)\); \} \}/);
  assert.match(css, /\.an::before\{/);
  assert.match(css, /\.an::after\{[^}]*border-top: 18px solid/);
  assert.doesNotMatch(css, /\.vt-/);
});

test("announcements follow the catalog in every menu", () => {
  const link = /href="\/catalog">(<span class="dpo-capsule-label">)?\{CATALOG_LINK_LABEL\}(<\/span>)?<\/a> <a href=\{ANNOUNCEMENTS_PATH\}>/;
  const landing = visibleText("components/landing/LandingHeader.astro");
  assert.equal(landing.match(new RegExp(link, "g"))?.length, 2);
  assert.match(
    visibleText("components/SiteHeader.astro"),
    /href="\/catalog">\{CATALOG_LINK_LABEL\}<\/a> <a class="nav-link" href=\{ANNOUNCEMENTS_PATH\}>\{ANNOUNCEMENTS_LINK_LABEL\}<\/a>/,
  );
});

test("landing strip leads to all starts on the announcements page", () => {
  const strip = visibleText("components/landing/StartsStrip.astro");
  assert.match(strip, /<a class="dpo-starts-all" href=\{ANNOUNCEMENTS_PATH\}>/);
  assert.doesNotMatch(strip, /sort=start/);
});

test("month chip follows the lowest month inside the active band", () => {
  const script = visibleText("scripts/starts-board.ts");
  assert.match(script, /return months\.filter\(\(month\) => inBand\.has\(month\)\)\.at\(-1\);/);
  assert.match(script, /const month = lowestInBand\(months, inBand\) \?\? firstWhenAbove\(months\);/);
  assert.doesNotMatch(script, /entries\.find\(/);
});
