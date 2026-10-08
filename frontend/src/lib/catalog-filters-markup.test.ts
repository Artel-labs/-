import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const SOURCE = new URL("../", import.meta.url);

function source(path: string): string {
  return readFileSync(new URL(path, SOURCE), "utf8");
}

test("catalog filters are four dropdowns in one bar instead of chip rows", () => {
  const bar = source("components/catalog/FilterBar.astro");
  assert.match(bar, /\["type", "Тип программы"\],\s*\["format", "Формат"\],\s*\["sphere", "Направление"\],\s*\["duration", "Длительность"\]/);
  assert.match(bar, /class="filter-bar" id="filters"/);
  assert.match(bar, /id="filterTags"[^>]*hidden/);
  assert.doesNotMatch(source("pages/catalog.astro"), /FilterRow/);
});

test("a dropdown lists checkboxes without the all option and applies by button", () => {
  const dropdown = source("components/catalog/FilterDropdown.astro");
  assert.match(dropdown, /chips\.filter\(\(chip\) => chip\.value !== ALL\)/);
  assert.match(dropdown, /aria-expanded="false" aria-controls=\{panelId\}/);
  assert.match(dropdown, /<input type="checkbox" name=\{group\} value=\{chip\.value\} data-value=\{chip\.value\} data-name=\{chip\.name\} \/>/);
  assert.match(dropdown, /data-filter-clear>Очистить</);
  assert.match(dropdown, /data-filter-apply>Применить</);
});

test("the filter bar no longer sticks to the top", () => {
  assert.doesNotMatch(source("styles/catalog.css"), /\.filters:first-of-type/);
  assert.doesNotMatch(source("styles/catalog-filters.css"), /sticky/);
});

test("analytics counts a checked option but not an unchecked one", () => {
  assert.match(source("scripts/analytics.ts"), /const unchecked = chip instanceof HTMLInputElement && !chip\.checked;/);
});

test("removed tags and resets go through one refresh of state", () => {
  const script = source("scripts/catalog-filters.ts");
  assert.match(script, /state\.active\[tag\.group\] = without\(state\.active\[tag\.group\], tag\.value\);\s*refresh\(elements, state\);/);
  assert.match(script, /parseValues\(params\.get\(dropdown\.group\), valuesOf\(dropdown\)\)/);
});
