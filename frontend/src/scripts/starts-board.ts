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

function followMonths(chips: HTMLElement[]): void {
  const byMonth = new Map(chips.map((chip) => [monthOf(chip), chip]));
  const observer = new IntersectionObserver(
    (entries) => {
      const visible = entries.find((entry) => entry.isIntersecting);
      const chip = visible ? byMonth.get(visible.target as HTMLElement) : undefined;
      if (chip) {
        press(chips, chip);
      }
    },
    { rootMargin: ACTIVE_BAND },
  );
  byMonth.forEach((_, month) => {
    if (month) {
      observer.observe(month);
    }
  });
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
