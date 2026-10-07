import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const SOURCE = new URL("../", import.meta.url);

function source(path: string): string {
  return readFileSync(new URL(path, SOURCE), "utf8");
}

test("high rating badge shows three stars with an explaining tooltip", () => {
  const badge = source("components/HighRatingBadge.astro");
  assert.match(badge, /const LABEL = "Программа с высоким рейтингом";/);
  assert.match(badge, /role="img" aria-label=\{LABEL\} data-tip=\{LABEL\} tabindex="0"/);
  assert.match(badge, /<span aria-hidden="true">★★★<\/span>/);
});

test("high rating stars are painted in the brand gold", () => {
  const css = source("styles/high-rating.css");
  assert.match(css, /^@layer widgets \{/);
  assert.match(css, /color: rgb\(var\(--ochre\)\);/);
  assert.match(css, /\.high-rating:focus::after/);
});

test("every high rating program tile on the landing carries the badge", () => {
  assert.match(source("components/landing/TopProgramTile.astro"), /<HighRatingBadge class="dpo-tile-rating" \/>/);
});

test("catalog card shows the badge outside the card link only for rated programs", () => {
  const card = source("components/catalog/ProgramCard.astro");
  assert.match(card, /\{card\.high_rating && <HighRatingBadge class="card-rating" \/>\}\n\s*<a href=\{href\} class="card-link">/);
});

test("program page shows the badge above the title only for rated programs", () => {
  const hero = source("components/program/ProgramHero.astro");
  assert.match(hero, /\{program\.high_rating && <HighRatingBadge class="hero-rating" \/>\}\n\s*<h1>/);
});
