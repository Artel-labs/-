import { keepAboveBars } from "./layout";
import { BotPanel } from "./panel";

let panel: BotPanel | null = null;

function toggle(trigger: HTMLElement): void {
  if (panel) {
    panel.close();
    return;
  }
  panel = new BotPanel(trigger, () => {
    panel = null;
  });
  panel.open();
}

export function setupSupportBot(): void {
  document.addEventListener("click", (event) => {
    const trigger = event.target instanceof Element ? event.target.closest<HTMLElement>("[data-bot-open]") : null;
    if (!trigger) {
      return;
    }
    event.preventDefault();
    toggle(trigger);
  });
  const reposition = (): void => {
    keepAboveBars(panel?.root ?? null);
  };
  new MutationObserver(reposition).observe(document, { childList: true, subtree: true });
  window.addEventListener("resize", reposition);
  reposition();
}
