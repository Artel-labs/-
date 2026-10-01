const HEADER_HEIGHT_VARIABLE = "--header-h";

function syncHeaderHeight(header: HTMLElement): void {
  const height = Math.round(header.getBoundingClientRect().height);
  if (height > 0) {
    document.documentElement.style.setProperty(HEADER_HEIGHT_VARIABLE, `${String(height)}px`);
  }
}

export function trackHeaderHeight(): void {
  const header = document.querySelector<HTMLElement>("header");
  if (!header) {
    return;
  }
  const sync = (): void => {
    syncHeaderHeight(header);
  };
  sync();
  window.addEventListener("resize", sync);
  document.getElementById("viToggle")?.addEventListener("click", () => window.setTimeout(sync, 0));
  void document.fonts.ready.then(sync);
}
