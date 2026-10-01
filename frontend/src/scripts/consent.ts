const STORAGE_KEY = "cookie-consent";

export function forgetConsent(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    return;
  }
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
