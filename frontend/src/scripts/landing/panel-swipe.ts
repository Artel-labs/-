import { prefersTouchMotion, projectedPosition, rubberBand, Spring, VelocityTracker } from "../spring";

const DEFAULT_PANEL_HEIGHT = 400;
const DRAG_THRESHOLD_PX = 10;
const SCROLL_TOLERANCE_PX = 4;
const CLICK_GUARD_MS = 120;
const DISMISS_SHARE = 0.35;
const MAX_DOWNWARD_VELOCITY = 100;
const EXIT_MARGIN_PX = 60;
const EXIT_RESPONSE = 0.3;
const RETURN_RESPONSE = 0.35;
const FADE_SHARE = 0.9;

export function attachPanelSwipe(panel: HTMLElement, onDismiss: () => void): void {
  if (panel.dataset.dpoSheet || !prefersTouchMotion()) {
    return;
  }
  panel.dataset.dpoSheet = "1";
  const height = (): number => panel.offsetHeight || DEFAULT_PANEL_HEIGHT;
  const spring = new Spring((position) => {
    panel.style.transform = position ? `translateY(${position.toFixed(2)}px)` : "";
    panel.style.opacity = position < 0 ? String(Math.max(0, 1 + position / (height() * FADE_SHARE))) : "";
  });
  const tracker = new VelocityTracker();
  let tracking = false;
  let engaged = false;
  let startY = 0;
  let grab = 0;
  let swallowClick = false;

  const scrollable = (): boolean => panel.scrollHeight > panel.clientHeight + SCROLL_TOLERANCE_PX;
  const syncTouchAction = (): void => {
    panel.style.touchAction = scrollable() ? "" : "none";
  };
  const resetStyles = (): void => {
    panel.style.transition = "";
    panel.style.transform = "";
    panel.style.opacity = "";
  };

  syncTouchAction();
  panel.addEventListener("click", () => window.requestAnimationFrame(syncTouchAction));
  panel.addEventListener(
    "click",
    (event) => {
      if (swallowClick) {
        swallowClick = false;
        event.preventDefault();
        event.stopPropagation();
      }
    },
    true,
  );

  panel.addEventListener("pointerdown", (event) => {
    if (!event.isPrimary || scrollable()) {
      return;
    }
    tracking = true;
    engaged = false;
    startY = event.clientY;
    spring.stop();
    tracker.start(event.timeStamp, spring.position);
  });

  panel.addEventListener("pointermove", (event) => {
    if (!tracking || !event.isPrimary) {
      return;
    }
    if (!engaged) {
      if (Math.abs(event.clientY - startY) < DRAG_THRESHOLD_PX) {
        return;
      }
      engaged = true;
      grab = event.clientY - spring.position;
      panel.style.transition = "none";
      panel.setPointerCapture(event.pointerId);
    }
    const raw = event.clientY - grab;
    spring.set(raw <= 0 ? raw : rubberBand(raw));
    tracker.add(event.timeStamp, raw);
  });

  const release = (event: PointerEvent): void => {
    if (!tracking || !event.isPrimary) {
      return;
    }
    tracking = false;
    if (!engaged) {
      return;
    }
    engaged = false;
    swallowClick = true;
    window.setTimeout(() => {
      swallowClick = false;
    }, CLICK_GUARD_MS);
    spring.velocity = tracker.velocity();
    if (projectedPosition(spring.position, spring.velocity) < -height() * DISMISS_SHARE && spring.velocity < MAX_DOWNWARD_VELOCITY) {
      spring.animate(-(height() + EXIT_MARGIN_PX), EXIT_RESPONSE, () => {
        panel.style.transition = "";
        onDismiss();
        panel.style.opacity = "";
      });
    } else {
      spring.animate(0, RETURN_RESPONSE, resetStyles);
    }
  };
  panel.addEventListener("pointerup", release);
  panel.addEventListener("pointercancel", release);
}
