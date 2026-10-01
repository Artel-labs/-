const PLACED_CLASS = "is-placed";

function pixels(value: string | undefined): string {
  return `${value ?? "0"}px`;
}

function place(element: HTMLElement): void {
  const { left, width, pin } = element.dataset;
  if (left !== undefined) {
    element.style.left = pixels(left);
  }
  if (width !== undefined) {
    element.style.width = pixels(width);
  }
  if (pin !== undefined) {
    element.style.setProperty("--tl-pin", pixels(pin));
  }
}

export function placeTimeline(): void {
  const timeline = document.querySelector<HTMLElement>(".tl");
  if (!timeline) {
    return;
  }
  place(timeline);
  timeline.querySelectorAll<HTMLElement>("[data-left], [data-width], [data-pin]").forEach(place);
  timeline.classList.add(PLACED_CLASS);
}
