export interface Suppressible {
  hidden: boolean;
  hide(): void;
  show(): void;
}

const live: Suppressible[] = [];

export function register(item: Suppressible): void {
  live.push(item);
}

export function unregister(item: Suppressible): void {
  const index = live.indexOf(item);
  if (index !== -1) {
    live.splice(index, 1);
  }
}

export function suppressOthers(newcomer: Suppressible): Suppressible[] {
  const suppressed = live.filter((item) => item !== newcomer && !item.hidden);
  suppressed.forEach((item) => {
    item.hide();
  });
  return suppressed;
}

export function restore(items: Suppressible[]): void {
  items.filter((item) => live.includes(item)).forEach((item) => {
    item.show();
  });
}
