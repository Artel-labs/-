import { PALETTE_HEX } from "../../lib/brand";
interface TelegramButton {
  show(): void;
  hide(): void;
  onClick(callback: () => void): void;
  setParams(params: Record<string, unknown>): void;
}

interface TelegramUser {
  first_name?: string;
  last_name?: string;
}

interface WebApp {
  initData: string;
  initDataUnsafe: { start_param?: string; user?: TelegramUser };
  MainButton: TelegramButton;
  BackButton: TelegramButton;
  HapticFeedback?: { notificationOccurred(type: string): void };
  ready(): void;
  expand(): void;
  openLink(url: string): void;
  isVersionAtLeast?(version: string): boolean;
  setBackgroundColor(color: string): void;
  setHeaderColor(color: string): void;
  setBottomBarColor?(color: string): void;
}

declare global {
  interface Window {
    Telegram?: { WebApp?: WebApp };
  }
}

const BACKGROUND_VERSION = "6.1";
const HEADER_VERSION = "6.9";
const BOTTOM_BAR_VERSION = "7.10";

export class Bridge {
  readonly app: WebApp | null;
  private mainAction: (() => void) | null = null;
  private readonly bar = document.querySelector<HTMLElement>(".bar");
  private readonly barBack = document.querySelector<HTMLButtonElement>(".bar-back");
  private readonly mainWrap = document.querySelector<HTMLElement>(".main-btn");
  private readonly mainButton = this.mainWrap?.querySelector("button") ?? null;

  constructor() {
    const app = window.Telegram?.WebApp;
    this.app = app?.initData ? app : null;
  }

  get inTelegram(): boolean {
    return this.app !== null;
  }

  startParam(): string | null {
    return this.app ? (this.app.initDataUnsafe.start_param ?? null) : new URLSearchParams(window.location.search).get("startapp");
  }

  user(): TelegramUser | null {
    return this.app?.initDataUnsafe.user ?? null;
  }

  connect(onBack: () => void): void {
    const runMain = (): void => {
      this.mainAction?.();
    };
    if (this.app) {
      this.decorate(this.app);
      this.app.MainButton.onClick(runMain);
      this.app.BackButton.onClick(onBack);
      return;
    }
    if (this.bar) {
      this.bar.hidden = false;
    }
    this.mainButton?.addEventListener("click", runMain);
    this.barBack?.addEventListener("click", onBack);
  }

  setMain(label: string | null, action: () => void = () => undefined): void {
    this.mainAction = label ? action : null;
    if (this.app) {
      if (label) {
        this.app.MainButton.setParams({ text: label, color: PALETTE_HEX["hse-blue-2"], text_color: PALETTE_HEX["hse-white"], is_active: true, is_visible: true });
      } else {
        this.app.MainButton.hide();
      }
      return;
    }
    if (this.mainWrap && this.mainButton) {
      this.mainWrap.hidden = !label;
      this.mainButton.textContent = label ?? "";
    }
    document.body.classList.toggle("has-main", Boolean(label));
  }

  setBack(visible: boolean): void {
    if (this.app) {
      if (visible) {
        this.app.BackButton.show();
      } else {
        this.app.BackButton.hide();
      }
      return;
    }
    if (this.barBack) {
      this.barBack.hidden = !visible;
    }
  }

  open(url: string | null): void {
    if (!url) {
      return;
    }
    if (this.app) {
      this.app.openLink(url);
    } else {
      window.open(url, "_blank", "noopener");
    }
  }

  routeLink(link: HTMLAnchorElement): void {
    link.addEventListener("click", (event) => {
      if (!this.app) {
        return;
      }
      event.preventDefault();
      this.app.openLink(link.href);
    });
  }

  haptic(type: "error" | "success"): void {
    this.app?.HapticFeedback?.notificationOccurred(type);
  }

  private decorate(app: WebApp): void {
    app.ready();
    app.expand();
    if (app.isVersionAtLeast?.(BACKGROUND_VERSION)) {
      app.setBackgroundColor(PALETTE_HEX["hse-white"]);
    }
    if (app.isVersionAtLeast?.(HEADER_VERSION)) {
      app.setHeaderColor(PALETTE_HEX["hse-white"]);
    }
    if (app.isVersionAtLeast?.(BOTTOM_BAR_VERSION)) {
      app.setBottomBarColor?.(PALETTE_HEX["hse-white"]);
    }
  }
}
