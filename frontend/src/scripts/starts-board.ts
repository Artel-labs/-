const LOOK_AHEAD_PX = 24;
const FIRST_ITEM_MARGIN_PX = 20;
const END_TOLERANCE_PX = 2;

function scrollOf(chip: HTMLElement): number {
  return Number(chip.dataset.scroll);
}

function press(chips: HTMLElement[], current: HTMLElement): void {
  chips.forEach((chip) => {
    chip.setAttribute("aria-pressed", String(chip === current));
  });
}

function revealFirstItem(wrap: HTMLElement): void {
  const first = wrap.querySelector<HTMLElement>(".tl-item");
  if (first && !wrap.scrollLeft && first.offsetLeft + first.offsetWidth > wrap.clientWidth) {
    wrap.scrollTo({ left: Math.max(0, first.offsetLeft - FIRST_ITEM_MARGIN_PX), behavior: "instant" });
  }
}

function visibleChip(wrap: HTMLElement, chips: HTMLElement[]): HTMLElement | undefined {
  if (wrap.scrollLeft >= wrap.scrollWidth - wrap.clientWidth - END_TOLERANCE_PX) {
    return chips.at(-1);
  }
  const position = wrap.scrollLeft + LOOK_AHEAD_PX;
  return chips.filter((chip) => scrollOf(chip) <= position).at(-1) ?? chips[0];
}

function followScroll(wrap: HTMLElement, chips: HTMLElement[]): void {
  let ticking = false;
  wrap.addEventListener(
    "scroll",
    () => {
      if (ticking) {
        return;
      }
      ticking = true;
      window.requestAnimationFrame(() => {
        ticking = false;
        const current = visibleChip(wrap, chips);
        if (current) {
          press(chips, current);
        }
      });
    },
    { passive: true },
  );
}

export function setupStartsBoard(): void {
  const wrap = document.querySelector<HTMLElement>(".tl-wrap");
  const chips = [...document.querySelectorAll<HTMLElement>(".starts-chip[data-scroll]")];
  if (!wrap || chips.length === 0) {
    return;
  }
  revealFirstItem(wrap);
  followScroll(wrap, chips);
  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      press(chips, chip);
      wrap.scrollTo({ left: scrollOf(chip), behavior: "smooth" });
    });
  });
}
