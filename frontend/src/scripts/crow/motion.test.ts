import assert from "node:assert/strict";
import { test } from "node:test";

import { bell, blinkAt, clamp, ease, outCubic, talk } from "./motion.ts";
import { blendPoses, restPose } from "./pose.ts";

test("clamp держит значение в границах", () => {
  assert.equal(clamp(-1, 0, 1), 0);
  assert.equal(clamp(2, 0, 1), 1);
  assert.equal(clamp(0.4, 0, 1), 0.4);
});

test("кривые начинаются в нуле и заканчиваются в единице", () => {
  assert.equal(ease(0), 0);
  assert.equal(ease(1), 1);
  assert.equal(ease(0.5), 0.5);
  assert.equal(outCubic(0), 0);
  assert.equal(outCubic(1), 1);
  assert.ok(Math.abs(bell(0)) < 1e-9);
  assert.equal(bell(0.5), 1);
});

test("моргание короткое и повторяется с периодом", () => {
  assert.equal(blinkAt(0.06, 4.1), 1);
  assert.equal(blinkAt(1, 4.1), 0);
  assert.equal(blinkAt(4.1 + 0.06, 4.1), blinkAt(0.06, 4.1));
});

test("клюв молчит вне реплики", () => {
  assert.equal(talk(-0.1, 1), 0);
  assert.equal(talk(1.1, 1), 0);
  assert.ok(talk(0.5, 1) > 0);
});

test("смешивание поз идёт от исходной к целевой", () => {
  const from = restPose();
  const to = { ...restPose(), rx: 100, op: 0 };
  assert.deepEqual(blendPoses(from, to, 0), from);
  assert.deepEqual(blendPoses(from, to, 1), to);
  assert.equal(blendPoses(from, to, 0.5).rx, 50);
});
