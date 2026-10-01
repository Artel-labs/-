const ASKQ_KEY = "crow-askq-shown";
const ASKQ_MS = 30 * 24 * 3600 * 1000;

export function askAlreadyShown(): boolean {
  try {
    const shownAt = Number(localStorage.getItem(ASKQ_KEY) ?? 0);
    return shownAt > 0 && Date.now() - shownAt < ASKQ_MS;
  } catch {
    return false;
  }
}

export function rememberAskShown(): void {
  try {
    localStorage.setItem(ASKQ_KEY, String(Date.now()));
  } catch {
    return;
  }
}
