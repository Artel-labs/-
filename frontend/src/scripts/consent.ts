const STORAGE_KEY = "cookie-consent";
const ACCEPTED = "accepted";
const DECLINED = "declined";
const CONSENT_EVENT = "dpo:consent";
const POLL_MS = 150;
const FONT_WAIT_MS = 3000;
const FONT_CHECKS = ['15px "HSE Sans"', '600 15px "HSE Sans"'];

type Answer = typeof ACCEPTED | typeof DECLINED;

function storedConsent(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function store(answer: Answer): void {
  try {
    localStorage.setItem(STORAGE_KEY, answer);
  } catch {
    return;
  }
}

export function forgetConsent(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    return;
  }
}

export function consentAccepted(): boolean {
  return storedConsent() === ACCEPTED;
}

export function onConsentAccepted(callback: () => void): void {
  window.addEventListener(CONSENT_EVENT, (event) => {
    if (event instanceof CustomEvent && event.detail === ACCEPTED) {
      callback();
    }
  });
}

export function consentAnswered(): boolean {
  const stored = storedConsent();
  return stored === ACCEPTED || stored === DECLINED;
}

export function whenConsentAnswered(callback: () => void): void {
  if (consentAnswered()) {
    callback();
    return;
  }
  window.addEventListener(CONSENT_EVENT, callback, { once: true });
}

function fontsLoaded(): boolean {
  try {
    return FONT_CHECKS.every((font) => document.fonts.check(font));
  } catch {
    return true;
  }
}

function afterFonts(callback: () => void): void {
  let waited = 0;
  const timer = window.setInterval(() => {
    waited += POLL_MS;
    if (fontsLoaded() || waited >= FONT_WAIT_MS) {
      window.clearInterval(timer);
      callback();
    }
  }, POLL_MS);
}

function answer(banner: HTMLElement, choice: Answer): void {
  store(choice);
  banner.remove();
  window.dispatchEvent(new CustomEvent(CONSENT_EVENT, { detail: choice }));
}

function bind(banner: HTMLElement, selector: string, choice: Answer): void {
  banner.querySelector(selector)?.addEventListener("click", () => {
    answer(banner, choice);
  });
}

export function setupCookieBanner(): void {
  const banner = document.getElementById("cookieBanner");
  if (!banner) {
    return;
  }
  if (consentAnswered()) {
    banner.remove();
    return;
  }
  bind(banner, ".cb-accept", ACCEPTED);
  bind(banner, ".cb-decline", DECLINED);
  window.setTimeout(() => {
    afterFonts(() => {
      banner.hidden = false;
    });
  }, POLL_MS);
}

export function setupConsentReset(): void {
  document.querySelectorAll<HTMLElement>("[data-consent-reset]").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      forgetConsent();
      window.location.reload();
    });
  });
}
