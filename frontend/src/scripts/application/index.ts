import {
  CHOOSER_TITLE,
  PROGRAM_TOPIC,
  needsPrograms,
  routeFor,
  type ApplicationRequest,
  type ProgramChoice,
  type Route,
} from "../../lib/hse-forms";
import { closeButton, element, openDialog, type Dialog } from "../dialog";
import { attachSheet } from "../sheet-gesture";
import { buildChooser } from "./chooser";
import { HSE_LINK, HSE_TEXT, LOADING_TEXT, PRIVACY_NOTE } from "./constants";
import { loadPrograms } from "./programs";
import { mountForm } from "./frame";

const TRIGGER = "[data-application],[data-application-topic]";

function requestOf(trigger: HTMLElement): ApplicationRequest {
  return {
    topic: trigger.dataset.applicationTopic ?? PROGRAM_TOPIC,
    kind: trigger.dataset.applicationKind ?? "",
    programId: trigger.dataset.programId ?? "",
  };
}

class ApplicationDialog {
  private readonly sheet = element("div", "dpo-app");
  private readonly title = element("h2", "", CHOOSER_TITLE);
  private readonly caption = element("p", "dpo-app-program");
  private readonly body = element("div", "dpo-app-body");
  private readonly dialog: Dialog;

  constructor(opener: HTMLElement) {
    const close = closeButton("dpo-app-close", "Закрыть окно");
    const backdrop = element("div", "dpo-app-backdrop");
    this.sheet.setAttribute("role", "dialog");
    this.sheet.setAttribute("aria-modal", "true");
    this.sheet.setAttribute("aria-labelledby", "dpo-app-title");
    this.title.id = "dpo-app-title";
    this.title.tabIndex = -1;
    this.sheet.append(close, this.title, this.caption, this.body, element("p", "dpo-app-note", PRIVACY_NOTE));
    backdrop.appendChild(this.sheet);
    this.body.appendChild(element("p", "dpo-app-loading", LOADING_TEXT));
    this.dialog = openDialog({ backdrop, initialFocus: this.title, opener });
    close.addEventListener("click", () => {
      this.dialog.close();
    });
    attachSheet({ root: backdrop, sheet: this.sheet, grip: "#dpo-app-title, .dpo-app-program", onClose: () => this.dialog.close() });
  }

  show(route: Route, programs: readonly ProgramChoice[]): void {
    if (route.kind === "form") {
      this.heading(route.title, route.caption);
      mountForm(this.body, route.form, route.fallback);
    } else if (route.kind === "hse") {
      this.heading(route.title, route.caption);
      this.body.replaceChildren(hseLink(route.href));
    } else if (route.kind === "choose") {
      this.heading(CHOOSER_TITLE, "");
      this.body.replaceChildren(
        buildChooser(programs, (program) => {
          this.show(routeFor({ topic: PROGRAM_TOPIC, kind: "", programId: program.id }, programs), programs);
          this.title.focus();
        }),
      );
    }
  }

  private heading(title: string, caption: string): void {
    this.title.textContent = title;
    this.caption.textContent = caption;
    this.caption.hidden = !caption;
  }
}

function hseLink(href: string): HTMLElement {
  const note = element("p", "dpo-app-hse", HSE_TEXT);
  const link = element("a", "dpo-app-link", HSE_LINK);
  link.href = href;
  link.target = "_blank";
  link.rel = "noopener";
  note.append(" ", link);
  return note;
}

async function openApplication(request: ApplicationRequest, opener: HTMLElement): Promise<void> {
  const quick = routeFor(request, []);
  if (quick.kind === "mail") {
    window.location.href = quick.href;
    return;
  }
  const dialog = new ApplicationDialog(opener);
  const programs = needsPrograms(request) ? await loadPrograms() : [];
  dialog.show(routeFor(request, programs), programs);
}

export function setupApplicationForm(): void {
  document.addEventListener("click", (event) => {
    const trigger = event.target instanceof Element ? event.target.closest<HTMLElement>(TRIGGER) : null;
    if (!trigger) {
      return;
    }
    event.preventDefault();
    void openApplication(requestOf(trigger), trigger);
  });
}
