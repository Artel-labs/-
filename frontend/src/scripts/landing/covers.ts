const TRACK_LOOKAHEAD_PX = 600;
const COVER_MARGIN = "400px 0px";

function paint(element: HTMLElement): void {
  const src = element.dataset.dpoCover ?? "";
  if (!src) {
    return;
  }
  const webp = element.dataset.dpoCoverWebp ?? "";
  element.style.backgroundImage = webp ? `image-set(url("${webp}") type("image/webp"), url("${src}"))` : `url("${src}")`;
}

function paintAhead(track: HTMLElement): void {
  const box = track.getBoundingClientRect();
  track.querySelectorAll<HTMLElement>("[data-dpo-cover]").forEach((element) => {
    const rect = element.getBoundingClientRect();
    if (rect.right > box.left - TRACK_LOOKAHEAD_PX && rect.left < box.right + TRACK_LOOKAHEAD_PX) {
      paint(element);
    }
  });
}

function watchTrack(track: HTMLElement): void {
  let ticking = false;
  track.addEventListener(
    "scroll",
    () => {
      if (ticking) {
        return;
      }
      ticking = true;
      window.requestAnimationFrame(() => {
        ticking = false;
        paintAhead(track);
      });
    },
    { passive: true },
  );
}

export function setupCovers(): void {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!(entry.target instanceof HTMLElement) || !entry.isIntersecting) {
          return;
        }
        paint(entry.target);
        const track = entry.target.closest<HTMLElement>(".dpo-top5-track");
        if (track) {
          paintAhead(track);
        }
        observer.unobserve(entry.target);
      });
    },
    { rootMargin: COVER_MARGIN },
  );
  document.querySelectorAll<HTMLElement>("[data-dpo-cover]").forEach((element) => {
    observer.observe(element);
  });
  document.querySelectorAll<HTMLElement>(".dpo-top5-track").forEach(watchTrack);
}
