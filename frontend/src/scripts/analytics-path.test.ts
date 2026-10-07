import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { KEPT_PARAMS, keptQuery } from "./analytics-path.ts";

const SHARED = JSON.parse(readFileSync(new URL("../../../shared/analytics-params.json", import.meta.url), "utf8")) as {
  kept: string[];
};

test("only utm parameters leave the browser", () => {
  assert.equal(keptQuery("?email=a@b.ru&utm_source=tg&phone=79990000000"), "?utm_source=tg");
});

test("page without utm parameters is sent as a bare path", () => {
  assert.equal(keptQuery("?email=a@b.ru"), "");
  assert.equal(keptQuery(""), "");
});

test("all three utm parameters are kept", () => {
  assert.equal(keptQuery("?utm_campaign=c&utm_medium=m&utm_source=s"), "?utm_source=s&utm_medium=m&utm_campaign=c");
});

test("browser and server keep the same parameters", () => {
  assert.deepEqual(KEPT_PARAMS, SHARED.kept);
});
