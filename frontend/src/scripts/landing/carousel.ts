import { prefersReducedMotion } from "./motion";

const STEP_RATIO = 0.86;
const MIN_STEP_PX = 240;
const HOLD_AFTER_CLICK_MS = 1200;
const DEFAULT_SPEED_PX_PER_SECOND = 26;
const MAX_FRAME_SECONDS = 0.05;
const VISIBLE_THRESHOLD = 0.15;
const DRIFT_TOLERANCE_PX = 2;
const EDGE_PX = 1;
const LOOP_ATTRIBUTE = "data-dpo-loop";
const STOPPED_ATTRIBUTE = "data-dpo-stopped";

interface LoopState {
  position: number | null;
  holdUntil: number;
  visible: boolean;
}

const loops = new WeakMap<HTMLElement, LoopState>();
const coarsePointer = window.matchMedia("(hover: none), (pointer: coarse)");

function trackFor(button: Element): HTMLElement | null {
  const id = button.getAttribute("aria-controls");
  return id ? document.getElementById(id) : null;
}

function loopState(track: HTMLElement): LoopState {
  let state = loops.get(track);
  if (!state) {
    state = { position: null, holdUntil: 0, visible: false };
    loops.set(track, state);
  }
  return state;
}

function syncButtons(track: HTMLElement): void {
  if (!track.id) {
    return;
  }
  const looped = track.hasAttribute(LOOP_ATTRIBUTE);
  const overflowing = track.scrollWidth > track.clientWidth + EDGE_PX;
  document.querySelectorAll<HTMLButtonElement>(`[aria-controls="${track.id}"][data-dpo-scroll]`).forEach((button) => {
    if (looped) {
      button.disabled = false;
      return;
    }
    const atStart = track.scrollLeft <= EDGE_PX;
    const atEnd = track.scrollLeft + track.clientWidth >= track.scrollWidth - EDGE_PX;
    button.disabled = (button.dataset.dpoScroll === "prev" ? atStart : atEnd) || !overflowing;
  });
}

function onScrollButton(event: MouseEvent): void {
  const button = event.target instanceof Element ? event.target.closest("[data-dpo-scroll]") : null;
  const track = button ? trackFor(button) : null;
  if (!button || !track) {
    return;
  }
  event.preventDefault();
  const delta = Math.max(MIN_STEP_PX, Math.round(track.clientWidth * STEP_RATIO));
  if (track.hasAttribute(LOOP_ATTRIBUTE)) {
    loopState(track).holdUntil = performance.now() + HOLD_AFTER_CLICK_MS;
  }
  track.scrollBy({
    left: button.getAttribute("data-dpo-scroll") === "prev" ? -delta : delta,
    behavior: prefersReducedMotion() ? "auto" : "smooth",
  });
}

function onPauseButton(event: MouseEvent): void {
  const button = event.target instanceof Element ? event.target.closest("[data-dpo-pause]") : null;
  const track = button ? trackFor(button) : null;
  if (!track) {
    return;
  }
  const stopped = track.toggleAttribute(STOPPED_ATTRIBUTE);
  document.querySelectorAll(`[aria-controls="${track.id}"][data-dpo-pause]`).forEach((pause) => {
    pause.setAttribute("aria-pressed", String(stopped));
    pause.setAttribute("aria-label", stopped ? "Запустить ленту" : "Остановить ленту");
    pause.classList.toggle("is-stopped", stopped);
  });
}

function paused(track: HTMLElement): boolean {
  return track.hasAttribute(STOPPED_ATTRIBUTE) || track.matches(":hover") || track.contains(document.activeElement);
}

function autoplayAllowed(): boolean {
  return !prefersReducedMotion() && !coarsePointer.matches && !document.documentElement.classList.contains("vi-mode") && !document.hidden;
}

function advance(track: HTMLElement, now: number, seconds: number): void {
  const state = loopState(track);
  const half = track.scrollWidth / 2;
  if (!state.visible || paused(track) || now < state.holdUntil || half < EDGE_PX) {
    return;
  }
  if (state.position === null || Math.abs(state.position - track.scrollLeft) > DRIFT_TOLERANCE_PX) {
    state.position = track.scrollLeft;
  }
  const speed = Number(track.dataset.dpoSpeed) || DEFAULT_SPEED_PX_PER_SECOND;
  state.position += speed * seconds;
  if (state.position >= half) {
    state.position -= half;
  }
  track.scrollLeft = state.position;
}

function startAutoplay(tracks: HTMLElement[]): void {
  let last: number | null = null;
  const step = (now: number): void => {
    const seconds = last === null ? 0 : Math.min((now - last) / 1000, MAX_FRAME_SECONDS);
    last = now;
    if (autoplayAllowed()) {
      tracks.forEach((track) => {
        advance(track, now, seconds);
      });
    }
    window.requestAnimationFrame(step);
  };
  window.requestAnimationFrame(step);
}

function watchVisibility(tracks: HTMLElement[]): void {
  let started = false;
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.target instanceof HTMLElement) {
          loopState(entry.target).visible = entry.isIntersecting;
        }
        if (entry.isIntersecting && !started) {
          started = true;
          startAutoplay(tracks);
        }
      });
    },
    { threshold: VISIBLE_THRESHOLD },
  );
  tracks.forEach((track) => {
    observer.observe(track);
  });
}

function wrapLoop(event: Event): void {
  const track = event.target;
  if (!(track instanceof HTMLElement) || !track.hasAttribute(LOOP_ATTRIBUTE)) {
    return;
  }
  const half = track.scrollWidth / 2;
  if (half < EDGE_PX) {
    return;
  }
  if (track.scrollLeft >= half) {
    track.scrollLeft -= half;
  } else if (track.scrollLeft < 0.5) {
    track.scrollLeft += half;
  }
}

export function setupCarousels(): void {
  document.addEventListener("click", onScrollButton);
  document.addEventListener("click", onPauseButton);
  document.addEventListener(
    "scroll",
    (event) => {
      if (event.target instanceof HTMLElement && event.target.classList.contains("dpo-track")) {
        syncButtons(event.target);
      }
    },
    true,
  );
  document.addEventListener("scroll", wrapLoop, true);
  const syncAll = (): void => {
    document.querySelectorAll<HTMLElement>(".dpo-track").forEach(syncButtons);
  };
  window.addEventListener("resize", syncAll);
  syncAll();
  const looped = [...document.querySelectorAll<HTMLElement>(`[${LOOP_ATTRIBUTE}]`)];
  watchVisibility(looped);
}
