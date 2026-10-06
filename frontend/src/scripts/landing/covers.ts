const COVER_MARGIN = "400px 0px";

function paint(element: HTMLElement): void {
  const src = element.dataset.dpoCover ?? "";
  if (!src) {
    return;
  }
  const webp = element.dataset.dpoCoverWebp ?? "";
  element.style.backgroundImage = webp ? `image-set(url("${webp}") type("image/webp"), url("${src}"))` : `url("${src}")`;
}

export function setupCovers(): void {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!(entry.target instanceof HTMLElement) || !entry.isIntersecting) {
          return;
        }
        paint(entry.target);
        observer.unobserve(entry.target);
      });
    },
    { rootMargin: COVER_MARGIN },
  );
  document.querySelectorAll<HTMLElement>("[data-dpo-cover]").forEach((element) => {
    observer.observe(element);
  });
}
