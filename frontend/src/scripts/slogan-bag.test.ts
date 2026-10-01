import assert from "node:assert/strict";
import { test } from "node:test";

import { drawBag, next, type Slogan } from "./slogan-bag.ts";

const SLOGANS: Slogan[] = [
  { text: "а", weight: 1 },
  { text: "б", weight: 1 },
  { text: "в", weight: 2 },
];

function sequence(values: number[]): () => number {
  let at = 0;
  return () => values[at++ % values.length] ?? 0;
}

test("мешок содержит каждую фразу столько раз, каков её вес", () => {
  const bag = drawBag(SLOGANS, null, sequence([0.1, 0.7, 0.3, 0.9]));
  assert.deepEqual([...bag].sort(), [0, 1, 2, 2]);
});

test("фраза с большим весом не идёт дважды подряд", () => {
  const bag = drawBag(SLOGANS, null, sequence([0.5]));
  bag.slice(1).forEach((index, at) => assert.notEqual(index, bag[at]));
});

test("новый мешок не начинается с последней показанной фразы", () => {
  for (let last = 0; last < SLOGANS.length; last += 1) {
    assert.notEqual(drawBag(SLOGANS, last, sequence([0.2, 0.8]))[0], last);
  }
});

test("следующая фраза берётся из сохранённого мешка", () => {
  const picked = next(SLOGANS, { bag: [1, 2], last: 0 });
  assert.equal(picked.index, 1);
  assert.deepEqual(picked.state, { bag: [2], last: 1 });
});

test("испорченное состояние не ломает выбор", () => {
  const picked = next(SLOGANS, { bag: [7, -1], last: 9 }, sequence([0.4]));
  assert.ok(picked.index >= 0 && picked.index < SLOGANS.length);
});
