import { whenConsentAnswered } from "../consent";

const DISMISS_KEY = "channel-invite-closed";
const DISMISS_MS = 30 * 24 * 3600 * 1000;
const SHOW_DELAY_MS = 1000;
const PLACE_INTERVAL_MS = 500;
const HERO_PASSED_PX = 120;
const HERO_FALLBACK_RATIO = 0.85;
const EDGE_PX = 16;
const GAP_PX = 12;

function dismissedRecently(): boolean {
  try {
    const dismissedAt = Number(localStorage.getItem(DISMISS_KEY) ?? 0);
    return dismissedAt > 0 && Date.now() - dismissedAt < DISMISS_MS;
  } catch {
    return false;
  }
}

function rememberDismissal(): void {
  try {
    localStorage.setItem(DISMISS_KEY, String(Date.now()));
  } catch {
    return;
  }
}

function topOf(node: HTMLElement | null): number | null {
  if (!node?.offsetHeight) {
    return null;
  }
  const rect = node.getBoundingClientRect();
  return rect.height ? rect.top : null;
}

function bottomOffset(): string {
  const tops = [topOf(document.getElementById("cookieBanner")), topOf(document.querySelector<HTMLElement>(".dpo-mobile-cta"))].filter(
    (value): value is number => value !== null,
  );
  if (!tops.length) {
    return `${String(EDGE_PX)}px`;
  }
  const overlap = window.innerHeight - Math.min(...tops);
  return `${String(Math.max(EDGE_PX, overlap + GAP_PX))}px`;
}

function keepAboveBottomBars(box: HTMLElement, badge: HTMLElement): void {
  const place = (): void => {
    const bottom = bottomOffset();
    box.style.bottom = bottom;
    badge.style.bottom = bottom;
  };
  place();
  const timer = window.setInterval(() => {
    if (!box.isConnected && !badge.isConnected) {
      window.clearInterval(timer);
      return;
    }
    place();
  }, PLACE_INTERVAL_MS);
  window.addEventListener("resize", place);
}

class ChannelInvite {
  private manualOpen = false;
  private ticking = false;
  private readonly hero = document.getElementById("top");
  private readonly onScroll = (): void => {
    if (this.ticking) {
      return;
    }
    this.ticking = true;
    requestAnimationFrame(() => {
      this.ticking = false;
      if (this.manualOpen && !this.pastHero()) {
        this.manualOpen = false;
      }
      this.sync();
    });
  };

  constructor(
    private readonly box: HTMLElement,
    private readonly badge: HTMLElement,
  ) {}

  show(): void {
    this.box.hidden = false;
    this.badge.addEventListener("click", () => {
      this.openManually();
    });
    this.box.querySelector(".ci-close")?.addEventListener("click", () => {
      this.dismiss();
    });
    this.box.querySelector(".ci-join")?.addEventListener("click", () => {
      this.dismiss();
    });
    window.addEventListener("scroll", this.onScroll, { passive: true });
    this.sync();
    requestAnimationFrame(() => {
      this.box.classList.add("is-open");
    });
    keepAboveBottomBars(this.box, this.badge);
  }

  private pastHero(): boolean {
    if (!this.hero) {
      return window.scrollY > window.innerHeight * HERO_FALLBACK_RATIO;
    }
    return this.hero.getBoundingClientRect().bottom < HERO_PASSED_PX;
  }

  private sync(): void {
    const collapsed = !this.manualOpen && this.pastHero();
    this.box.classList.toggle("ci-collapsed", collapsed);
    const wasOn = this.badge.classList.contains("ci-on");
    this.badge.classList.toggle("ci-on", collapsed);
    if (collapsed && !wasOn) {
      requestAnimationFrame(() => {
        this.badge.classList.add("ci-in");
      });
    }
    if (!collapsed) {
      this.badge.classList.remove("ci-in");
    }
  }

  private openManually(): void {
    this.manualOpen = true;
    this.sync();
    this.box.querySelector<HTMLElement>(".ci-join")?.focus();
  }

  private dismiss(): void {
    rememberDismissal();
    this.box.remove();
    this.badge.remove();
    window.removeEventListener("scroll", this.onScroll);
  }
}

export function setupChannelInvite(): void {
  const box = document.getElementById("channelInvite");
  const badge = document.getElementById("channelInviteBadge");
  if (!box || !badge) {
    return;
  }
  if (dismissedRecently()) {
    box.remove();
    badge.remove();
    return;
  }
  const invite = new ChannelInvite(box, badge);
  whenConsentAnswered(() => {
    window.setTimeout(() => {
      invite.show();
    }, SHOW_DELAY_MS);
  });
}
