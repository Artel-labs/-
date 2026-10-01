const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
const OPEN_CLASS = "is-open";
const CLOSE_DELAY_MS = 240;

export interface DialogOptions {
  backdrop: HTMLElement;
  initialFocus: HTMLElement;
  opener?: Element | null;
  onClosed?: () => void;
}

export interface Dialog {
  close: (restoreFocus?: boolean) => void;
}

interface Inerted {
  node: Element;
  ariaHidden: string | null;
}

function inertSiblings(except: HTMLElement): Inerted[] {
  return [...document.body.children]
    .filter((node) => node !== except)
    .map((node) => {
      const saved = { node, ariaHidden: node.getAttribute("aria-hidden") };
      node.setAttribute("aria-hidden", "true");
      if (node instanceof HTMLElement) {
        node.inert = true;
      }
      return saved;
    });
}

function restore(saved: Inerted[]): void {
  saved.forEach(({ node, ariaHidden }) => {
    if (ariaHidden === null) {
      node.removeAttribute("aria-hidden");
    } else {
      node.setAttribute("aria-hidden", ariaHidden);
    }
    if (node instanceof HTMLElement) {
      node.inert = false;
    }
  });
}

function focusables(container: HTMLElement): HTMLElement[] {
  return [...container.querySelectorAll<HTMLElement>(FOCUSABLE)].filter(
    (node) => node.offsetParent !== null || node === document.activeElement,
  );
}

function trapTab(event: KeyboardEvent, container: HTMLElement): void {
  const items = focusables(container);
  const first = items[0];
  const last = items.at(-1);
  if (!first || !last) {
    return;
  }
  const active = document.activeElement;
  const outside = !items.some((item) => item === active);
  if (event.shiftKey && (active === first || outside)) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && (active === last || outside)) {
    event.preventDefault();
    first.focus();
  }
}

export function openDialog({ backdrop, initialFocus, opener = document.activeElement, onClosed }: DialogOptions): Dialog {
  let closed = false;
  let pressedOutside = false;
  backdrop.dataset.dialogOpen = "true";
  document.body.appendChild(backdrop);
  const saved = inertSiblings(backdrop);
  document.documentElement.style.overflow = "hidden";

  const onKey = (event: KeyboardEvent): void => {
    if (event.key === "Escape") {
      event.preventDefault();
      close();
    } else if (event.key === "Tab") {
      trapTab(event, backdrop);
    }
  };

  const close = (restoreFocus = true): void => {
    if (closed) {
      return;
    }
    closed = true;
    document.removeEventListener("keydown", onKey, true);
    restore(saved);
    document.documentElement.style.overflow = "";
    backdrop.classList.remove(OPEN_CLASS);
    backdrop.dataset.dialogOpen = "false";
    window.setTimeout(() => {
      if (backdrop.dataset.dialogOpen === "false") {
        backdrop.remove();
      }
    }, CLOSE_DELAY_MS);
    if (restoreFocus && opener instanceof HTMLElement && document.contains(opener)) {
      opener.focus();
    }
    onClosed?.();
  };

  backdrop.addEventListener("mousedown", (event) => {
    pressedOutside = event.target === backdrop;
  });
  backdrop.addEventListener("click", (event) => {
    if (event.target === backdrop && pressedOutside) {
      close();
    }
  });
  document.addEventListener("keydown", onKey, true);
  window.requestAnimationFrame(() => {
    backdrop.classList.add(OPEN_CLASS);
    initialFocus.focus();
  });
  return { close };
}

export function element<K extends keyof HTMLElementTagNameMap>(tag: K, className = "", text = ""): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) {
    node.className = className;
  }
  if (text) {
    node.textContent = text;
  }
  return node;
}

export function closeButton(className: string, label: string): HTMLButtonElement {
  const button = element("button", className, "×");
  button.type = "button";
  button.setAttribute("aria-label", label);
  return button;
}
