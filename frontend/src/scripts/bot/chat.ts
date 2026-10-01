import type { CrowMascot } from "../crow/mascot";
import { reducedMotion } from "./crows";
import { node, programCard, typingDots } from "./view";
import type { BotProgram } from "./types";

const TYPING_MS = 520;

export class Chat {
  readonly log = node("div", "dpo-bot-log");
  private closed = false;

  constructor(private readonly headCrow: () => CrowMascot | null) {
    this.log.setAttribute("aria-live", "polite");
  }

  close(): void {
    this.closed = true;
  }

  say(text: string): void {
    this.log.append(node("p", "dpo-bot-say", text));
  }

  mine(text: string): void {
    this.log.append(node("p", "dpo-bot-mine", text));
  }

  add(...elements: HTMLElement[]): void {
    this.log.append(...elements);
  }

  cards(programs: BotProgram[]): void {
    this.add(...programs.map(programCard));
  }

  scrollDown(): void {
    this.log.scrollTop = this.log.scrollHeight;
  }

  respond(render: () => void): void {
    if (this.closed) {
      return;
    }
    if (reducedMotion()) {
      render();
      this.scrollDown();
      return;
    }
    const dots = typingDots();
    this.add(dots);
    this.headCrow()?.play("think");
    this.scrollDown();
    window.setTimeout(() => {
      if (this.closed) {
        return;
      }
      dots.remove();
      const applyBefore = this.applyCount();
      render();
      this.headCrow()?.play(this.applyCount() > applyBefore ? "point" : "nod");
      this.scrollDown();
    }, TYPING_MS);
  }

  private applyCount(): number {
    return this.log.querySelectorAll(".dpo-bot-apply").length;
  }
}
