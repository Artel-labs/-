import { trackEvent } from "../analytics";
import type { CrowMascot } from "../crow/mascot";
import { mountDoneCrow, mountErrorCrow } from "../crow/inline";
import { closeButton, element, openDialog, type Dialog } from "../dialog";
import { attachSheet } from "../sheet-gesture";
import { ANONYMOUS_TOPICS, CORPORATE, PERSONAL, PERSONAL_CLASS, PROGRAM_TOPIC, TOPIC_HINTS, TOPIC_TITLES } from "./constants";
import { showDone } from "./done";
import { buildForm } from "./form";
import { fillPrograms, loadPrograms, programOption } from "./programs";
import { submit, type ChosenProgram } from "./submit";

const TRIGGER = "[data-application],[data-application-topic]";
const NO_PROGRAM_HINT = "Расскажите о себе — учебный офис свяжется с вами и подберёт программу.";

interface Context {
  programId: string;
  programTitle: string;
  programUrl: string;
  topic: string;
  kind: string;
}

function contextOf(trigger: HTMLElement): Context {
  return {
    programId: trigger.dataset.programId ?? "",
    programTitle: trigger.dataset.programTitle ?? "",
    programUrl: trigger.dataset.programUrl ?? window.location.href,
    topic: trigger.dataset.applicationTopic ?? PROGRAM_TOPIC,
    kind: trigger.dataset.applicationKind ?? PERSONAL,
  };
}

class ApplicationDialog {
  private readonly sheet = element("div", "dpo-app");
  private readonly title = element("h2", "", TOPIC_TITLES[PROGRAM_TOPIC]);
  private readonly caption = element("p", "dpo-app-program");
  private readonly form: HTMLFormElement;
  private readonly dialog: Dialog;
  private doneCrow: CrowMascot | null = null;
  private errorCrow: CrowMascot | null = null;

  constructor(private readonly context: Context, opener: HTMLElement) {
    this.form = buildForm({ onTopic: (topic) => this.applyTopic(topic), onKind: (kind) => this.applyKind(kind, true) });
    const close = closeButton("dpo-app-close", "Закрыть форму");
    this.sheet.setAttribute("role", "dialog");
    this.sheet.setAttribute("aria-modal", "true");
    this.sheet.setAttribute("aria-labelledby", "dpo-app-title");
    this.title.id = "dpo-app-title";
    this.title.tabIndex = -1;
    this.sheet.append(close, this.title, this.caption, this.form);
    const backdrop = element("div", "dpo-app-backdrop");
    backdrop.appendChild(this.sheet);
    this.form.addEventListener("submit", (event) => {
      event.preventDefault();
      void submit(this.form, this.chosenProgram(), {
        onDone: () => {
          this.doneCrow = mountDoneCrow(showDone(this.sheet, this.context.topic, this.chosenProgram().title));
        },
        onFailed: (status, invalidFields) => {
          if (!invalidFields) {
            trackEvent({ type: "form_error", label: `http ${String(status)}` });
          }
          this.shakeCrow();
        },
      });
    });
    this.select<HTMLSelectElement>("#dpo-app-topic").value = context.topic;
    this.select<HTMLSelectElement>("#dpo-app-kind").value = context.kind;
    this.applyTopic(context.topic);
    this.applyKind(context.kind, false);
    this.dialog = openDialog({ backdrop, initialFocus: this.title, opener, onClosed: () => this.releaseCrow() });
    close.addEventListener("click", () => {
      this.dialog.close();
    });
    attachSheet({ root: backdrop, sheet: this.sheet, grip: "#dpo-app-title, .dpo-app-program", onClose: () => this.dialog.close() });
    void loadPrograms().then((items) => {
      fillPrograms(this.programSelect(), items);
      this.preselectProgram();
    });
  }

  private releaseCrow(): void {
    this.doneCrow?.destroy();
    this.doneCrow = null;
    this.errorCrow?.destroy();
    this.errorCrow = null;
  }

  private shakeCrow(): void {
    const anchor = this.form.querySelector<HTMLElement>(".dpo-app-error-crow");
    if (!anchor || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return;
    }
    this.errorCrow ??= mountErrorCrow(anchor);
    this.errorCrow.play("shake");
  }

  private select<T extends HTMLElement>(selector: string): T {
    const node = this.sheet.querySelector<T>(selector);
    if (!node) {
      throw new Error(`Нет элемента формы ${selector}`);
    }
    return node;
  }

  private programSelect(): HTMLSelectElement {
    return this.select<HTMLSelectElement>("#dpo-app-program");
  }

  private hasProgramList(): boolean {
    return this.programSelect().options.length > 1;
  }

  private applyTopic(topic: string): void {
    this.context.topic = topic;
    const isProgram = topic === PROGRAM_TOPIC;
    this.title.textContent = TOPIC_TITLES[topic] ?? TOPIC_TITLES[PROGRAM_TOPIC] ?? "";
    this.select("#dpo-app-program-wrap").hidden = !(isProgram && this.hasProgramList());
    this.select("#dpo-app-kind-wrap").hidden = !isProgram;
    this.select("#dpo-app-corp").hidden = !isProgram || this.select<HTMLSelectElement>("#dpo-app-kind").value !== CORPORATE;
    this.applyAnonymity(ANONYMOUS_TOPICS.includes(topic));
    this.updateCaption(isProgram);
  }

  private applyAnonymity(anonymous: boolean): void {
    this.form.querySelectorAll<HTMLElement>(`.${PERSONAL_CLASS}`).forEach((node) => {
      node.hidden = anonymous;
      node.querySelectorAll("input").forEach((input) => {
        input.disabled = anonymous;
      });
    });
    this.select("#dpo-app-comment-hint").hidden = !anonymous;
  }

  private updateCaption(isProgram: boolean): void {
    if (!isProgram) {
      this.caption.hidden = false;
      this.caption.textContent = TOPIC_HINTS[this.context.topic] ?? "";
      return;
    }
    const hasList = this.hasProgramList();
    this.caption.hidden = hasList;
    if (hasList) {
      this.caption.textContent = "";
    } else {
      this.caption.textContent = this.context.programTitle ? `Программа: ${this.context.programTitle}` : NO_PROGRAM_HINT;
    }
  }

  private applyKind(kind: string, focusFirst: boolean): void {
    this.context.kind = kind;
    const corporate = kind === CORPORATE && this.context.topic === PROGRAM_TOPIC;
    const block = this.select("#dpo-app-corp");
    block.hidden = !corporate;
    if (!corporate) {
      return;
    }
    if (focusFirst) {
      block.querySelector("input")?.focus();
    }
  }

  private preselectProgram(): void {
    const select = this.programSelect();
    const { programId, programTitle, programUrl } = this.context;
    if (programId) {
      const known = [...select.options].find((option) => option.value === programId);
      if (!known && programTitle) {
        select.appendChild(programOption(programId, programTitle, programUrl));
      }
      select.value = programId;
    } else {
      select.value = "";
    }
    this.applyTopic(this.context.topic);
  }

  private chosenProgram(): ChosenProgram {
    const select = this.programSelect();
    const wrap = this.select("#dpo-app-program-wrap");
    const option = select.selectedOptions[0];
    if (!wrap.hidden && select.value && option) {
      return { id: select.value, title: option.textContent, url: absolute(option.dataset.url ?? "") };
    }
    const { programId, programTitle, programUrl } = this.context;
    return { id: programId, title: programTitle, url: programId ? absolute(programUrl) : programUrl || window.location.href };
  }
}

function absolute(href: string): string {
  if (!href) {
    return window.location.href;
  }
  try {
    return new URL(href, window.location.href).href;
  } catch {
    return href;
  }
}

function openApplication(context: Context, opener: HTMLElement): ApplicationDialog {
  return new ApplicationDialog(context, opener);
}

export function setupApplicationForm(): void {
  document.addEventListener("click", (event) => {
    const trigger = event.target instanceof Element ? event.target.closest<HTMLElement>(TRIGGER) : null;
    if (!trigger || (!trigger.hasAttribute("data-application") && !trigger.dataset.applicationTopic)) {
      return;
    }
    event.preventDefault();
    openApplication(contextOf(trigger), trigger);
  });
}
