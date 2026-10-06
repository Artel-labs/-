import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const SOURCES = new URL("../", import.meta.url);

function source(path: string): string {
  return readFileSync(new URL(path, SOURCES), "utf8");
}

test("program reviews use the landing review card in a swipe-only strip", () => {
  const section = source("components/program/ReviewsSection.astro");
  assert.match(section, /import ReviewFigure from "\.\.\/ReviewFigure\.astro"/);
  assert.match(section, /class="dpo-reviews-track" role="region" aria-label="Отзывы выпускников" tabindex="0"/);
  assert.doesNotMatch(section, /data-dpo-scroll|data-dpo-loop|data-dpo-pause|<ul class="reviews">/);
});

test("review card links to the programme only when it knows the programme", () => {
  assert.match(source("components/ReviewFigure.astro"), /review\.path && review\.program && \(/);
});

test("landing and programme pages share the review strip styles", () => {
  assert.match(source("pages/index.astro"), /import "\.\.\/styles\/reviews\.css";/);
  assert.match(source("pages/programs/[page].astro"), /import "\.\.\/\.\.\/styles\/reviews\.css";/);
  assert.doesNotMatch(source("styles/landing.css"), /\.dpo-reviews-track \{|\.dpo-review \{/);
  assert.doesNotMatch(source("styles/program.css"), /\.reviews\{|\.review-author\{/);
});

test("programme review cards line up with the block heading", () => {
  assert.match(source("styles/program.css"), /\.block \.dpo-review\{margin:0 20px 0 0\}/);
});
