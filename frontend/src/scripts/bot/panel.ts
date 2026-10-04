import type { CrowMascot } from "../crow/mascot";
import { attachSheet } from "../sheet-gesture";
import { renderPickProgram, renderPriceRange, renderReply, renderUpcomingStarts } from "./answers";
import { Chat } from "./chat";
import { bringLauncherBack, mountHeadCrow, sendLauncherAway } from "./crows";
import { loadBotData } from "./data";
import { keepAboveBars } from "./layout";
import { ActionQueue } from "./queue.ts";
import { detectIntent, reply, type Intent } from "./reply.ts";
import type { BotData } from "./types";
import { applyButton, choiceButton, node } from "./view";

const GREETING = "Спрашивайте про программы: тему, формат, цену или ближайший старт.";
const HINTS = ["Подобрать программу", "Онлайн", "Какой документ выдают", "Ближайшие старты", "Сколько стоит"];
const FAIL_TEXT = "Не получилось загрузить программы. Напишите нам — ответим.";
const WAIT_TEXT = "Секунду, гружу программы…";
const FOCUSABLE = 'a[href],button:not([disabled]),input,[tabindex]:not([tabindex="-1"])';
const OPEN_CLASS = "is-open";
const INTENT_RENDERERS: Record<Intent, (chat: Chat, data: BotData) => void> = {
  pickProgram: renderPickProgram,
  upcomingStarts: renderUpcomingStarts,
  priceRange: renderPriceRange,
};

function setLaunchersExpanded(expanded: boolean): void {
  document.querySelectorAll("[data-bot-open]").forEach((launcher) => {
    launcher.setAttribute("aria-expanded", String(expanded));
  });
}

export class BotPanel {
  readonly root = node("div");
  private readonly queue = new ActionQueue<BotData>();
  private readonly chat = new Chat(() => this.headCrow);
  private readonly input = node("input");
  private headCrow: CrowMascot | null = null;
  private failureShown = false;
  private readonly onKeydown = (event: KeyboardEvent): void => {
    this.handleKey(event);
  };

  constructor(
    private readonly opener: HTMLElement | null,
    private readonly onClosed: () => void,
  ) {
    this.root.id = "dpoBotPanel";
    this.root.setAttribute("role", "dialog");
    this.root.setAttribute("aria-modal", "true");
    this.root.setAttribute("aria-label", "Поддержка");
  }

  open(): void {
    sendLauncherAway();
    const crowSlot = node("div", "dpo-bot-crow");
    crowSlot.setAttribute("aria-hidden", "true");
    this.root.append(this.head(crowSlot), this.chat.log, this.form());
    document.body.append(this.root);
    this.headCrow = mountHeadCrow(crowSlot);
    setLaunchersExpanded(true);
    document.addEventListener("keydown", this.onKeydown, true);
    attachSheet({ root: this.root, sheet: this.root, grip: "#dpoBotHead", onClose: () => this.close() });
    keepAboveBars(this.root);
    requestAnimationFrame(() => {
      this.root.classList.add(OPEN_CLASS);
    });
    this.greet();
    (this.root.querySelector<HTMLElement>(".dpo-bot-hints button") ?? this.input).focus();
    void loadBotData().then((data) => {
      if (data) {
        this.queue.resolve(data);
      } else {
        this.queue.reject();
      }
    });
  }

  close(): void {
    this.chat.close();
    this.headCrow?.destroy();
    this.headCrow = null;
    this.root.remove();
    setLaunchersExpanded(false);
    document.removeEventListener("keydown", this.onKeydown, true);
    bringLauncherBack();
    (this.opener ?? document.querySelector<HTMLElement>("[data-bot-open]"))?.focus();
    this.onClosed();
  }

  private head(crowSlot: HTMLElement): HTMLElement {
    const close = node("button", "dpo-bot-close", "×");
    close.type = "button";
    close.setAttribute("aria-label", "Закрыть окно поддержки");
    close.addEventListener("click", () => {
      this.close();
    });
    const brand = node("div", "dpo-bot-brand");
    brand.append(crowSlot, node("h2", "", "Поддержка"));
    const head = node("div");
    head.id = "dpoBotHead";
    head.append(brand, close);
    return head;
  }

  private form(): HTMLFormElement {
    this.input.type = "text";
    this.input.id = "dpoBotInput";
    this.input.placeholder = "Например: банкротство онлайн";
    this.input.setAttribute("aria-label", "Вопрос в поддержку");
    const submit = node("button", "", "Спросить");
    submit.type = "submit";
    const form = node("form");
    form.id = "dpoBotForm";
    form.append(this.input, submit);
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const value = this.input.value;
      this.input.value = "";
      this.ask(value);
    });
    return form;
  }

  private greet(): void {
    this.chat.say(GREETING);
    const row = node("div", "dpo-bot-hints");
    row.append(...HINTS.map((hint) => choiceButton(hint, () => this.ask(hint))));
    this.chat.add(row);
  }

  private ask(query: string): void {
    const text = query.trim();
    if (!text) {
      return;
    }
    this.chat.mine(text);
    const intent = detectIntent(text);
    this.whenReady((data) => {
      if (intent) {
        INTENT_RENDERERS[intent](this.chat, data);
        return;
      }
      renderReply(this.chat, reply(text, data));
      this.chat.scrollDown();
    });
  }

  private whenReady(action: (data: BotData) => void): void {
    const wasEmpty = this.queue.isEmpty();
    const status = this.queue.run(
      (data) => {
        this.chat.respond(() => {
          action(data);
        });
      },
      () => {
        this.showFailure();
      },
    );
    if (status === "queued" && wasEmpty) {
      this.chat.say(WAIT_TEXT);
    }
    this.chat.scrollDown();
  }

  private showFailure(): void {
    if (this.failureShown) {
      return;
    }
    this.failureShown = true;
    this.chat.respond(() => {
      this.chat.say(FAIL_TEXT);
      this.chat.add(applyButton());
    });
  }

  private handleKey(event: KeyboardEvent): void {
    if (event.key === "Escape") {
      if (document.querySelector(".dpo-app-backdrop")) {
        return;
      }
      event.preventDefault();
      this.close();
      return;
    }
    if (event.key === "Tab") {
      this.trapFocus(event);
    }
  }

  private trapFocus(event: KeyboardEvent): void {
    const items = this.root.querySelectorAll<HTMLElement>(FOCUSABLE);
    const first = items[0];
    const last = items[items.length - 1];
    if (!first || !last) {
      return;
    }
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }
}
