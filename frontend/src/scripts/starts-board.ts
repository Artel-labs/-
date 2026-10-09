import { prefersReducedMotion } from "./landing/motion";

const ACTIVE_BAND = "-20% 0px -60% 0px";

function press(chips: HTMLElement[], current: HTMLElement): void {
  chips.forEach((chip) => {
    chip.setAttribute("aria-pressed", String(chip === current));
  });
}

function monthOf(chip: HTMLElement): HTMLElement | null {
  const id = chip.dataset.target;
  return id ? document.getElementById(id) : null;
}

function lowestInBand(months: HTMLElement[], inBand: Set<Element>): HTMLElement | undefined {
  return months.filter((month) => inBand.has(month)).at(-1);
}

function firstWhenAbove(months: HTMLElement[]): HTMLElement | undefined {
  const first = months[0];
  return first && first.getBoundingClientRect().top > 0 ? first : undefined;
}

function followMonths(chips: HTMLElement[]): void {
  const byMonth = new Map(chips.map((chip) => [monthOf(chip), chip]));
  const months = [...byMonth.keys()].filter((month): month is HTMLElement => month !== null);
  const inBand = new Set<Element>();
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => (entry.isIntersecting ? inBand.add(entry.target) : inBand.delete(entry.target)));
      const month = lowestInBand(months, inBand) ?? firstWhenAbove(months);
      const chip = month ? byMonth.get(month) : undefined;
      if (chip) {
        press(chips, chip);
      }
    },
    { rootMargin: ACTIVE_BAND },
  );
  months.forEach((month) => observer.observe(month));
}

export function setupStartsBoard(): void {
  const chips = [...document.querySelectorAll<HTMLElement>(".starts-chip[data-target]")];
  if (chips.length === 0) {
    return;
  }
  followMonths(chips);
  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      press(chips, chip);
      monthOf(chip)?.scrollIntoView({ behavior: prefersReducedMotion() ? "auto" : "smooth", block: "start" });
    });
  });
}
