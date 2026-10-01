import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { emailLooksValid, phoneProblem } from "./form-rules.ts";

interface Cases {
  email: [string, boolean][];
  phone: [string, string][];
}

const CASES = JSON.parse(readFileSync(new URL("../../../shared/form-rules-cases.json", import.meta.url), "utf8")) as Cases;

test("почта проверяется так же, как на сервере", () => {
  CASES.email.forEach(([value, valid]) => assert.equal(emailLooksValid(value), valid, value));
});

test("телефон проверяется так же, как на сервере", () => {
  CASES.phone.forEach(([value, problem]) => assert.equal(phoneProblem(value), problem, value));
});
