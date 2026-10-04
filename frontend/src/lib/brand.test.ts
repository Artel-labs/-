import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { test } from "node:test";

import { PALETTE_HEX } from "./brand.ts";

const PALETTE_CSS = readFileSync(new URL("../styles/palette.css", import.meta.url), "utf8");

function triplet(token: string): string {
  const match = PALETTE_CSS.match(new RegExp(`--${token}:\\s*(\\d+ \\d+ \\d+);`));
  assert.ok(match?.[1], `в palette.css нет --${token}`);
  return match[1];
}

function hexTriplet(hex: string): string {
  return [1, 3, 5].map((start) => parseInt(hex.slice(start, start + 2), 16)).join(" ");
}

test("цвета для theme-color и Telegram совпадают с palette.css", () => {
  for (const [token, hex] of Object.entries(PALETTE_HEX)) {
    assert.equal(hexTriplet(hex), triplet(token), token);
  }
});

test("в стилях нет цветов в обход palette.css, кроме чёрного и белого", () => {
  const styles = new URL("../styles/", import.meta.url);
  const neutral = /^(#000|#fff|#000000|#ffffff)$/i;
  const sheets = readdirSync(styles).filter((name) => name.endsWith(".css") && name !== "palette.css");
  for (const name of sheets) {
    const css = readFileSync(new URL(name, styles), "utf8");
    const hexes = (css.match(/#[0-9a-f]{3,6}\b/gi) ?? []).filter((hex) => !neutral.test(hex));
    assert.deepEqual(hexes, [], name);
  }
});

const BRANDBOOK = new Set([
  "255 255 255",
  "0 0 0",
  "15 45 105",
  "35 75 155",
  "125 160 210",
  "205 220 240",
  "250 185 0",
  "255 220 145",
  "230 30 60",
  "146 146 146",
  "198 198 198",
]);
const KEPT_BY_DECISION = new Set(["night", "night-mid", "night-ink", "outline-dark"]);

test("в palette.css только цвета брендбука, кроме затемнения фото и маскота", () => {
  for (const [, token = "", value = ""] of PALETTE_CSS.matchAll(/--([a-z0-9-]+):\s*(\d+ \d+ \d+);/g)) {
    if (!KEPT_BY_DECISION.has(token)) {
      assert.ok(BRANDBOOK.has(value), `--${token}: ${value}`);
    }
  }
});
