import assert from "node:assert/strict";
import { test } from "node:test";

import { programIdFromPage, sitePath } from "./program.ts";

test("id берётся из адреса страницы программы", () => {
  assert.equal(programIdFromPage("angliyskoe-kontraktnoe-pravo-856421092"), "856421092");
  assert.equal(programIdFromPage("angliyskoe-kontraktnoe-pravo-856421092.html"), "856421092");
  assert.equal(programIdFromPage("856421092"), "856421092");
});

test("адрес без id не считается страницей программы", () => {
  assert.equal(programIdFromPage("x"), null);
  assert.equal(programIdFromPage("pravo-v2x"), null);
  assert.equal(programIdFromPage(""), null);
});

test("путь программы становится адресом от корня сайта", () => {
  assert.equal(sitePath("programs/neyropravo-905186485.html"), "/programs/neyropravo-905186485.html");
});
