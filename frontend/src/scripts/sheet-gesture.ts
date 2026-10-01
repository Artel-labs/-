import { prefersTouchMotion, projectedPosition, rubberBand, Spring, VelocityTracker } from "./spring";

const DEFAULT_SHEET_HEIGHT = 480;
const MIN_DISMISS_PX = 140;
const DISMISS_SHARE = 0.4;
const MAX_UPWARD_VELOCITY = -100;
const EXIT_MARGIN_PX = 40;
const EXIT_RESPONSE = 0.3;
const RETURN_RESPONSE = 0.35;
const MIN_OPACITY = 0.35;
const CONTROLS = "a, button, input, select, textarea";

export interface SheetOptions {
  root: HTMLElement;
  sheet: HTMLElement;
  grip: string;
  onClose: () => void;
}

export interface SheetControl {
  reset: () => void;
}

function addHandle(sheet: HTMLElement): HTMLElement {
  const handle = document.createElement("span");
  handle.className = "dpo-sheet-handle";
  handle.setAttribute("aria-hidden", "true");
  sheet.insertBefore(handle, sheet.firstChild);
  return handle;
}

export function attachSheet({ root, sheet, grip, onClose }: SheetOptions): SheetControl | null {
  if (!prefersTouchMotion()) {
    return null;
  }
  const handle = addHandle(sheet);
  sheet.querySelectorAll<HTMLElement>(grip).forEach((node) => {
    node.style.touchAction = "none";
  });
  const height = (): number => sheet.offsetHeight || DEFAULT_SHEET_HEIGHT;
  const spring = new Spring((position) => {
    sheet.style.transform = position ? `translateY(${position.toFixed(2)}px)` : "";
    const fade = Math.max(0, 1 - position / height());
    root.style.opacity = position > 0 ? String(MIN_OPACITY + (1 - MIN_OPACITY) * fade) : "";
  });
  const tracker = new VelocityTracker();
  let dragging = false;
  let grab = 0;

  const clearMotion = (): void => {
    sheet.style.transition = "";
    root.style.transition = "";
    sheet.style.transform = "";
    root.style.opacity = "";
  };

  root.addEventListener("pointerdown", (event) => {
    const target = event.target instanceof Element ? event.target : null;
    if (!event.isPrimary || !target || (target !== handle && !target.closest(grip)) || target.closest(CONTROLS)) {
      return;
    }
    dragging = true;
    spring.stop();
    grab = event.clientY - spring.position;
    tracker.start(event.timeStamp, spring.position);
    sheet.style.transition = "none";
    root.style.transition = "none";
    sheet.setPointerCapture(event.pointerId);
    event.preventDefault();
  });

  root.addEventListener("pointermove", (event) => {
    if (!dragging || !event.isPrimary) {
      return;
    }
    const raw = event.clientY - grab;
    spring.set(raw >= 0 ? raw : -rubberBand(-raw));
    tracker.add(event.timeStamp, raw);
  });

  const release = (event: PointerEvent): void => {
    if (!dragging || !event.isPrimary) {
      return;
    }
    dragging = false;
    spring.velocity = tracker.velocity();
    const dismissAt = Math.max(MIN_DISMISS_PX, height() * DISMISS_SHARE);
    if (projectedPosition(spring.position, spring.velocity) > dismissAt && spring.velocity > MAX_UPWARD_VELOCITY) {
      const exit = window.innerHeight - sheet.getBoundingClientRect().top + EXIT_MARGIN_PX;
      spring.animate(exit, EXIT_RESPONSE, () => {
        root.style.transition = "";
        onClose();
        root.style.opacity = "";
      });
    } else {
      spring.animate(0, RETURN_RESPONSE, clearMotion);
    }
  };
  root.addEventListener("pointerup", release);
  root.addEventListener("pointercancel", release);

  return {
    reset: () => {
      spring.stop();
      dragging = false;
      spring.velocity = 0;
      spring.set(0);
      clearMotion();
    },
  };
}
