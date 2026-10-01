import { prefersReducedMotion } from "./motion";

const GRIDS = [".dpo-spheres", ".dpo-formats"];
const VISIBLE_THRESHOLD = 0.1;

function watch(grid: HTMLElement): void {
  grid.classList.add("dpo-fly");
  const observer = new IntersectionObserver(
    (entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        grid.classList.add("is-in");
        observer.disconnect();
      }
    },
    { threshold: VISIBLE_THRESHOLD },
  );
  observer.observe(grid);
}

export function setupGridFly(): void {
  if (prefersReducedMotion()) {
    return;
  }
  GRIDS.forEach((selector) => {
    const grid = document.querySelector<HTMLElement>(selector);
    if (grid) {
      watch(grid);
    }
  });
}
