import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";
import { ANNOUNCEMENTS_PATH, CATALOG_PATH, LANDING_PATH, MAIN_NAV, type NavItem, RATINGS_PATH, isCurrent, navHref } from "./nav.ts";

const SOURCES = new URL("../", import.meta.url);

function source(path: string): string {
  return readFileSync(new URL(path, SOURCES), "utf8").replace(/\s+/g, " ");
}

test("main menu lists the landing items in order", () => {
  assert.deepEqual(
    MAIN_NAV.map((item) => item.label),
    ["Портфель программ", "Анонсы программ", "Форматы", "Преподаватели", "Рейтинги", "Контакты"],
  );
});

function item(label: string): NavItem {
  const found = MAIN_NAV.find((entry) => entry.label === label);
  assert.ok(found, label);
  return found;
}

test("landing sections are anchors on the landing and links to it elsewhere", () => {
  assert.equal(navHref(item("Форматы"), LANDING_PATH), "#formats");
  assert.equal(navHref(item("Форматы"), CATALOG_PATH), "/#formats");
  assert.equal(navHref(item("Портфель программ"), LANDING_PATH), "/catalog");
  assert.equal(navHref(item("Рейтинги"), ANNOUNCEMENTS_PATH), "/ratings");
});

test("only the page being viewed is marked as current", () => {
  assert.deepEqual(
    MAIN_NAV.filter((item) => isCurrent(item, RATINGS_PATH)).map((item) => item.label),
    ["Рейтинги"],
  );
  assert.deepEqual(
    MAIN_NAV.filter((item) => isCurrent(item, LANDING_PATH)),
    [],
  );
});

test("landing, catalog, announcements and ratings share one header", () => {
  assert.match(source("pages/index.astro"), /<MainHeader current=\{LANDING_PATH\} \/>/);
  assert.match(source("pages/catalog.astro"), /<MainHeader current=\{CATALOG_PATH\} \/>/);
  assert.match(source("pages/announcements.astro"), /<MainHeader current=\{ANNOUNCEMENTS_PATH\} \/>/);
  assert.match(source("pages/ratings.astro"), /<MainHeader slot="header" current=\{RATINGS_PATH\} \/>/);
  assert.match(source("pages/ratings.astro"), /<ApplicationForm slot="overlays" \/>/);
  assert.match(source("pages/programs/[page].astro"), /<SiteHeader/);
  assert.match(source("layouts/DocumentPage.astro"), /<slot name="header"><DocumentHeader \/><\/slot>/);
  for (const old of ["components/catalog/CatalogHeader.astro", "components/landing/LandingHeader.astro", "scripts/header-height.ts"]) {
    assert.ok(!existsSync(new URL(old, SOURCES)), old);
  }
});

test("header keeps the vision button and the application button instead of the home link", () => {
  const header = source("components/MainHeader.astro");
  assert.match(header, /<ViModeButton \/>/);
  assert.match(header, /<a class="dpo-nav-cta" data-application="" href=\{apply\}>Подать заявку<\/a>/);
  assert.match(header, /class:list=\{\{ "is-active": item\.page \}\} aria-current=\{item\.page\}/);
  assert.doesNotMatch(header, /HomeLink|На главную/);
});

test("burger script only handles the header menu", () => {
  assert.match(source("scripts/landing/nav-menu.ts"), /const TRIGGER = "\.dpo-header \[aria-controls\]\[aria-expanded\]";/);
});

test("header styles live in one file and stay apart from page headers", () => {
  const landing = source("styles/landing.css");
  assert.doesNotMatch(landing, /\.dpo-header|\.dpo-capsule|#viToggle|\.dpo-burger/);
  const header = source("styles/main-header.css");
  assert.match(header, /^@layer widgets, landing;/);
  assert.match(header, /@layer landing \{ html\.vi-mode \.dpo-burger span \{ background: #000 !important; \} html\.vi-mode #viToggle svg \{ display: block !important; \} \}/);
  assert.doesNotMatch(source("styles/catalog.css"), /(^|[\s}])header\{|--header-h/);
  assert.doesNotMatch(source("styles/document.css"), /(^|[\s}])header \{/);
  assert.match(source("components/document/DocumentHeader.astro"), /<header class="doc-header">/);
});
