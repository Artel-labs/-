import { FORM_MESSAGE, formPage } from "../../lib/hse-forms";
import { element } from "../dialog";
import { FAILED_LINK, FAILED_TEXT, FRAME_TITLE, LOADING_TEXT, WIDGET_TIMEOUT_MS } from "./constants";

interface FormSize {
  type: string;
  ready: boolean;
  height: number;
}

function failure(fallback: string): HTMLElement {
  const note = element("p", "dpo-app-failed", FAILED_TEXT);
  const link = element("a", "dpo-app-link", FAILED_LINK);
  link.href = fallback;
  link.target = "_blank";
  link.rel = "noopener";
  note.append(" ", link);
  return note;
}

function isFormSize(data: unknown): data is FormSize {
  return typeof data === "object" && data !== null && (data as FormSize).type === FORM_MESSAGE;
}

export function mountForm(container: HTMLElement, form: number, fallback: string): void {
  const loading = element("p", "dpo-app-loading", LOADING_TEXT);
  const frame = element("iframe", "dpo-app-frame");
  let ready = false;
  const onMessage = (event: MessageEvent): void => {
    if (!frame.isConnected) {
      window.removeEventListener("message", onMessage);
      return;
    }
    if (event.origin !== window.location.origin || event.source !== frame.contentWindow || !isFormSize(event.data)) {
      return;
    }
    frame.style.height = `${String(Math.ceil(event.data.height))}px`;
    if (event.data.ready && !ready) {
      ready = true;
      loading.remove();
      frame.classList.add("is-ready");
    }
  };
  frame.src = formPage(form);
  frame.title = FRAME_TITLE;
  window.addEventListener("message", onMessage);
  container.replaceChildren(loading, frame);
  window.setTimeout(() => {
    if (!ready && frame.isConnected) {
      window.removeEventListener("message", onMessage);
      container.replaceChildren(failure(fallback));
    }
  }, WIDGET_TIMEOUT_MS);
}
