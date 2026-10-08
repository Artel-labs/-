import assert from "node:assert/strict";
import { test } from "node:test";
import { parseValues, passes, without } from "./catalog-selection.ts";

const FORMATS = ["offline", "hybrid", "online", "mixed"];

test("an old single-value link still selects that value", () => {
  assert.deepEqual(parseValues("online", FORMATS), ["online"]);
});

test("several comma-separated values are selected in the list order", () => {
  assert.deepEqual(parseValues("mixed,online", FORMATS), ["online", "mixed"]);
});

test("the quiz value all and unknown values select nothing", () => {
  assert.deepEqual(parseValues("all", FORMATS), []);
  assert.deepEqual(parseValues("zoom,online", FORMATS), ["online"]);
  assert.deepEqual(parseValues(null, FORMATS), []);
});

test("an empty selection lets every card through", () => {
  assert.equal(passes([], "online"), true);
  assert.equal(passes([], undefined), true);
});

test("a card passes when its value is one of the selected", () => {
  assert.equal(passes(["online", "mixed"], "mixed"), true);
  assert.equal(passes(["online", "mixed"], "offline"), false);
  assert.equal(passes(["online"], undefined), false);
});

test("removing a value keeps the others", () => {
  assert.deepEqual(without(["online", "mixed"], "online"), ["mixed"]);
});
