import { consentAccepted, onConsentAccepted } from "./consent";

const ENDPOINT = "/api/collect";
const HEARTBEAT_MS = 15_000;
const FLUSH_MS = 8_000;
const PATH_CHECK_MS = 1_000;
const MAX_QUEUE = 30;
const REQUEUE_LIMIT = 10;
const SESSION_KEY = "dpo_sid";
const MOBILE_MAX = 768;
const TABLET_MAX = 1024;
const LANGUAGE_MAX = 16;
const LABEL_MAX = 120;
const SCROLL_MARKS = [25, 50, 75, 100];
const FULL = 100;
const RANDOM_TAIL = 8;

interface Payload {
  type: string;
  path?: string;
  title?: string;
  ref?: string;
  target?: string;
  label?: string;
  ms?: number;
  scroll?: number;
}

let started = false;
const queue: Record<string, unknown>[] = [];
let pageEntered = Date.now();
let maxScroll = 0;
let scrollMarks = new Set<number>();

function newSessionId(): string {
  if (typeof crypto.randomUUID === "function") {
    return crypto.randomUUID().replace(/-/g, "");
  }
  return `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 2 + RANDOM_TAIL)}`;
}

function sessionId(): string {
  try {
    let sid = sessionStorage.getItem(SESSION_KEY);
    if (!sid) {
      sid = newSessionId();
      sessionStorage.setItem(SESSION_KEY, sid);
    }
    return sid;
  } catch {
    return `tmp_${Date.now().toString(36)}`;
  }
}

function deviceType(): string {
  const width = Math.min(screen.width || 0, window.innerWidth || 0);
  if (width && width < MOBILE_MAX) {
    return "mobile";
  }
  return width && width < TABLET_MAX ? "tablet" : "desktop";
}

function pathName(): string {
  return location.pathname + location.search;
}

function referrerHost(): string {
  try {
    if (!document.referrer) {
      return "";
    }
    const url = new URL(document.referrer);
    return url.host === location.host ? "" : url.hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
}

function send(batch: Record<string, unknown>[], useBeacon: boolean): void {
  const body = JSON.stringify({ events: batch });
  if (useBeacon && navigator.sendBeacon(ENDPOINT, new Blob([body], { type: "application/json" }))) {
    return;
  }
  fetch(ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json" }, body, keepalive: true, credentials: "omit" }).catch(() => {
    if (queue.length < MAX_QUEUE) {
      queue.unshift(...batch.slice(0, REQUEUE_LIMIT));
    }
  });
}

function flush(useBeacon = false): void {
  if (!queue.length) {
    return;
  }
  send(queue.splice(0, MAX_QUEUE), useBeacon);
}

function enqueue(partial: Payload): void {
  if (!started) {
    return;
  }
  queue.push({
    t: Date.now(),
    sid: sessionId(),
    path: pathName(),
    title: document.title,
    ref: "",
    target: "",
    label: "",
    ms: 0,
    device: deviceType(),
    lang: navigator.language.slice(0, LANGUAGE_MAX),
    scroll: maxScroll,
    ...partial,
  });
  if (queue.length >= MAX_QUEUE) {
    flush(true);
  }
}

function dwellMs(): number {
  return Math.max(0, Date.now() - pageEntered);
}

function trackPageview(): void {
  pageEntered = Date.now();
  maxScroll = 0;
  scrollMarks = new Set();
  enqueue({ type: "pageview", ref: referrerHost() });
}

function trackScroll(): void {
  const height = Math.max(document.documentElement.scrollHeight, document.body.scrollHeight) - window.innerHeight;
  if (height <= 0) {
    return;
  }
  const percent = Math.min(FULL, Math.round((window.scrollY / height) * FULL));
  maxScroll = Math.max(maxScroll, percent);
  SCROLL_MARKS.filter((mark) => percent >= mark && !scrollMarks.has(mark)).forEach((mark) => {
    scrollMarks.add(mark);
    enqueue({ type: "scroll", scroll: mark, ms: dwellMs() });
  });
}

function isProgramLink(href: string): boolean {
  try {
    const url = new URL(href, location.href);
    return (/\.hse\.ru$/i.test(url.hostname) || url.hostname === "hse.ru") && /\/edu\/dpo\//i.test(url.pathname);
  } catch {
    return false;
  }
}

function linkLabel(link: HTMLAnchorElement): string {
  return link.querySelector("h3")?.textContent?.trim() || link.getAttribute("aria-label") || (link.textContent ?? "").trim().slice(0, LABEL_MAX);
}

function trackLink(link: HTMLAnchorElement): void {
  const label = linkLabel(link);
  if (isProgramLink(link.href) || link.classList.contains("card")) {
    enqueue({ type: "program", target: link.href, label: label || link.getAttribute("data-type") || "", title: label });
    return;
  }
  try {
    const url = new URL(link.href, location.href);
    if (url.origin !== location.origin) {
      enqueue({ type: "outbound", target: link.href, label });
    } else {
      enqueue({ type: "click", target: url.pathname + url.search, label });
    }
  } catch {
    enqueue({ type: "click", target: link.href, label });
  }
}

function trackChip(chip: HTMLElement): void {
  const value = chip.dataset.value;
  if (!value) {
    return;
  }
  const group = chip.closest<HTMLElement>("[data-group]")?.dataset.group ?? "filter";
  enqueue({ type: "filter", label: `${group}:${value}`, target: value });
}

function onClick(event: MouseEvent): void {
  const target = event.target instanceof Element ? event.target : null;
  const link = target?.closest<HTMLAnchorElement>("a[href]");
  if (link) {
    trackLink(link);
    return;
  }
  const chip = target?.closest<HTMLElement>(".chip, [data-value]");
  if (chip) {
    trackChip(chip);
  }
}

function heartbeat(): void {
  enqueue({ type: "heartbeat", ms: dwellMs(), scroll: maxScroll });
}

function watchPath(): void {
  let lastPath = pathName();
  window.setInterval(() => {
    const path = pathName();
    if (path !== lastPath) {
      enqueue({ type: "exit", ms: dwellMs(), path: lastPath, scroll: maxScroll });
      lastPath = path;
      trackPageview();
    }
  }, PATH_CHECK_MS);
}

function start(): void {
  if (started) {
    return;
  }
  started = true;
  trackPageview();
  document.addEventListener("click", onClick, { capture: true, passive: true });
  window.addEventListener("scroll", trackScroll, { passive: true });
  window.addEventListener("pagehide", () => {
    enqueue({ type: "exit", ms: dwellMs(), scroll: maxScroll });
    flush(true);
  });
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") {
      heartbeat();
      flush(true);
    }
  });
  window.setInterval(heartbeat, HEARTBEAT_MS);
  window.setInterval(() => {
    flush(false);
  }, FLUSH_MS);
  watchPath();
}

export function trackEvent(payload: Payload): void {
  enqueue(payload);
}

export function setupAnalytics(): void {
  if (consentAccepted()) {
    start();
    return;
  }
  onConsentAccepted(start);
}
