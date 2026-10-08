const TENS = 10;
const HUNDREDS = 100;
const FEW_MIN = 2;
const FEW_MAX = 4;
const TEENS_MIN = 11;
const TEENS_MAX = 14;

export function pluralRu(count: number, one: string, few: string, many: string): string {
  const lastTwo = Math.abs(count) % HUNDREDS;
  const last = lastTwo % TENS;
  if (lastTwo >= TEENS_MIN && lastTwo <= TEENS_MAX) {
    return many;
  }
  if (last === 1) {
    return one;
  }
  return last >= FEW_MIN && last <= FEW_MAX ? few : many;
}
