import { FORM_MESSAGE } from "../lib/hse-forms";

const RENDERED = ".pass-express-poll";
const CONTENT = ".hse-form";

function report(content: HTMLElement): void {
  const ready = document.querySelector(RENDERED) !== null;
  window.parent.postMessage({ type: FORM_MESSAGE, ready, height: content.offsetHeight }, window.location.origin);
}

export function reportFormSize(): void {
  const content = document.querySelector<HTMLElement>(CONTENT);
  if (!content) {
    return;
  }
  const send = (): void => {
    report(content);
  };
  new ResizeObserver(send).observe(content);
  new MutationObserver(send).observe(content, { childList: true, subtree: true });
  send();
}
