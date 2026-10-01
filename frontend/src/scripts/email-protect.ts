export function revealEmails(): void {
  document.querySelectorAll<HTMLAnchorElement>(".email-protect").forEach((link) => {
    const address = `${link.dataset.u ?? ""}@${link.dataset.d ?? ""}`;
    link.href = `mailto:${address}`;
    link.textContent = address;
  });
}
