import assert from "node:assert/strict";
import { test } from "node:test";
import { pluralRu } from "./plural.ts";

const word = (count: number): string => pluralRu(count, "программу", "программы", "программ");

test("russian plural picks one, few and many forms", () => {
  assert.equal(word(1), "программу");
  assert.equal(word(21), "программу");
  assert.equal(word(3), "программы");
  assert.equal(word(34), "программы");
  assert.equal(word(0), "программ");
  assert.equal(word(25), "программ");
});

test("eleven to fourteen take the many form", () => {
  assert.equal(word(11), "программ");
  assert.equal(word(12), "программ");
  assert.equal(word(114), "программ");
});
