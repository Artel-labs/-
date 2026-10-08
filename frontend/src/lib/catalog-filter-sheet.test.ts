import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const SOURCE = new URL("../", import.meta.url);

function source(path: string): string {
  return readFileSync(new URL(path, SOURCE), "utf8");
}

test("on a phone the dropdowns give way to one filters button", () => {
  const css = source("styles/catalog-filters.css");
  assert.match(css, /\.filter-sheet-open\{ display: none; \}/);
  assert.match(css, /@media \(max-width: 760px\)\{\s*\.filter-bar \.fd\{ display: none; \}\s*\.filter-sheet-open\{ display: inline-flex; \}/);
  assert.match(source("components/catalog/FilterBar.astro"), /class="fd-toggle filter-sheet-open" data-filter-sheet-open/);
});

test("the bottom bar filters link opens the sheet too", () => {
  assert.match(source("pages/catalog.astro"), /<a class="secondary" href="#filters" data-filter-sheet-open>Фильтры<\/a>/);
});

test("the sheet is a modal dialog that can be swiped away and shows a live count", () => {
  const sheet = source("scripts/catalog-sheet.ts");
  assert.match(sheet, /sheet\.setAttribute\("aria-modal", "true"\)/);
  assert.match(sheet, /attachSheet\(\{ root: parts\.backdrop, sheet: parts\.sheet/);
  assert.match(sheet, /`Показать \$\{String\(count\)\} \$\{pluralRu\(count, "программу", "программы", "программ"\)\}`/);
  assert.match(sheet, /parts\.sheet\.addEventListener\("change", update\)/);
});

test("the sheet builds its options from the dropdowns, not a second copy of markup", () => {
  assert.match(source("scripts/catalog-sheet.ts"), /dropdown\.boxes\.map\(\(box\) =>/);
});
