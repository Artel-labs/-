import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const SOURCE = fileURLToPath(new URL("..", import.meta.url));
const SPACED_DASH = /[А-Яа-яЁё»)] [–-] [А-Яа-яЁё«(]/;

function astroFiles(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      return astroFiles(path);
    }
    return entry.name.endsWith(".astro") ? [path] : [];
  });
}

test("в разметке нет тире с обычными пробелами и «© » без неразрывного пробела", () => {
  for (const file of astroFiles(SOURCE)) {
    const source = readFileSync(file, "utf8");
    assert.doesNotMatch(source, SPACED_DASH, file);
    assert.doesNotMatch(source, /© /, file);
  }
});
