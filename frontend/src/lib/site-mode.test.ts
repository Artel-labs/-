import assert from "node:assert/strict";
import { test } from "node:test";

import { PRODUCTION, TEST, demoClosed } from "./site-mode.ts";

test("Telegram demo is closed on a production server", () => {
  assert.equal(demoClosed(PRODUCTION), true);
});

test("Telegram demo stays open on a test server", () => {
  assert.equal(demoClosed(TEST), false);
});
