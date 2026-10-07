import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const BANNER = readFileSync(new URL("./CookieBanner.astro", import.meta.url), "utf8").replaceAll("&nbsp;", " ");

test("banner describes what the site really does", () => {
  assert.match(BANNER, /не использует cookies и сторонние счётчики/);
  assert.match(BANNER, /статистику посещений\s+на своём сервере, без IP-адресов/);
  assert.match(BANNER, /хранятся только в вашем браузере/);
});

test("banner does not mention Yandex Metrika", () => {
  assert.doesNotMatch(BANNER, /Метрик/);
  assert.doesNotMatch(BANNER, /используем cookies/);
});

test("banner buttons ask to allow or refuse statistics", () => {
  assert.match(BANNER, /class="cb-accept">Разрешить</);
  assert.match(BANNER, /class="cb-decline">Отказаться</);
});
