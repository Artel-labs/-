import { ICON_PATHS, ICON_STROKE, ICON_VIEWBOX, type IconName } from "../../lib/icons";
import { HSE_MARK, HSE_MARK_ALT, HSE_URL, LOCKUP_CAPTION } from "../../lib/brand";
import type { Bridge } from "./bridge";

type Child = Node | string | null | undefined | false;
type Attributes = Record<string, string | boolean | null | undefined>;

const SVG_NS = "http://www.w3.org/2000/svg";

export function h<K extends keyof HTMLElementTagNameMap>(tag: K, attributes: Attributes | null = null, children: Child[] = []): HTMLElementTagNameMap[K] {
  const element = document.createElement(tag);
  Object.entries(attributes ?? {}).forEach(([key, value]) => {
    if (value === null || value === undefined || value === false) {
      return;
    }
    if (key === "class") {
      element.className = String(value);
    } else if (key === "text") {
      element.textContent = String(value);
    } else {
      element.setAttribute(key, value === true ? "" : value);
    }
  });
  children.forEach((child) => {
    if (child === null || child === undefined || child === false || child === "") {
      return;
    }
    element.append(child);
  });
  return element;
}

export function picture(src: string | null): HTMLImageElement | null {
  return src ? h("img", { src, alt: "", loading: "lazy", decoding: "async" }) : null;
}

export function icon(name: IconName): SVGSVGElement {
  const svg = document.createElementNS(SVG_NS, "svg");
  const attributes: [string, string][] = [
    ["class", "icon"],
    ["viewBox", ICON_VIEWBOX],
    ["fill", "none"],
    ["stroke", "currentColor"],
    ["stroke-width", ICON_STROKE],
    ["stroke-linecap", "round"],
    ["stroke-linejoin", "round"],
    ["aria-hidden", "true"],
  ];
  attributes.forEach(([attribute, value]) => {
    svg.setAttribute(attribute, value);
  });
  const path = document.createElementNS(SVG_NS, "path");
  path.setAttribute("d", ICON_PATHS[name]);
  svg.append(path);
  return svg;
}

export function list(className: string, items: string[], tag: "ul" | "ol" = "ul", marker: IconName | null = null): HTMLElement | null {
  if (!items.length) {
    return null;
  }
  return h(tag, { class: className }, items.map((item) => h("li", null, [marker ? icon(marker) : null, item])));
}

export function section(title: string, sub: string | null, body: HTMLElement | null): HTMLElement | null {
  if (!body) {
    return null;
  }
  return h("section", { class: "block" }, [h("h2", { class: "h2", text: title }), sub ? h("p", { class: "sub", text: sub }) : null, body]);
}

export function clamped(className: string, text: string, limit: number): HTMLElement {
  const paragraph = h("p", { class: `${className} clamp`, text });
  if (text.length <= limit) {
    paragraph.classList.remove("clamp");
    return paragraph;
  }
  const more = h("button", { class: "more", type: "button", "aria-expanded": "false", text: "Читать полностью" });
  more.addEventListener("click", () => {
    const open = !paragraph.classList.toggle("clamp");
    more.textContent = open ? "Свернуть" : "Читать полностью";
    more.setAttribute("aria-expanded", String(open));
  });
  return h("div", null, [paragraph, more]);
}

export function plural(count: number, one: string, few: string, many: string): string {
  const last = count % 10;
  const lastTwo = count % 100;
  const word = last === 1 && lastTwo !== 11 ? one : last >= 2 && last <= 4 && (lastTwo < 12 || lastTwo > 14) ? few : many;
  return `${String(count)} ${word}`;
}

export function hostOf(url: string): string {
  try {
    return new URL(url).host.replace(/^www\./, "");
  } catch {
    return "";
  }
}

export function outLink(bridge: Bridge, className: string | null, href: string, children: (Node | string | null)[]): HTMLAnchorElement {
  const link = h("a", { class: className, href, target: "_blank", rel: "noopener noreferrer" }, children);
  bridge.routeLink(link);
  return link;
}

export function hseLockup(bridge: Bridge): HTMLElement {
  const mark = h("img", { src: HSE_MARK, width: "44", height: "44", alt: HSE_MARK_ALT });
  return h("div", { class: "hse-lockup" }, [
    outLink(bridge, "hse-lockup-mark", HSE_URL, [mark]),
    h("span", { class: "hse-lockup-caption" }, LOCKUP_CAPTION.map((line) => h("span", { text: line }))),
  ]);
}
