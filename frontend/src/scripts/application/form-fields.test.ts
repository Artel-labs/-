import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

function source(name: string): string {
  return readFileSync(new URL(name, import.meta.url), "utf8");
}

test("application form does not ask for a job title", () => {
  for (const name of ["form.ts", "submit.ts"]) {
    assert.doesNotMatch(source(name), /position|Должность/i, name);
  }
});

test("application form does not ask how the applicant found the centre", () => {
  for (const name of ["form.ts", "submit.ts", "constants.ts"]) {
    assert.doesNotMatch(source(name), /sources|sourceOther|узнали/i, name);
  }
});
