import type { SitemapEntry } from "./site";

const XML_ESCAPES: Record<string, string> = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&apos;",
};

function escapeXml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => XML_ESCAPES[char] ?? char);
}

function url(entry: SitemapEntry): string {
  return [
    "  <url>",
    `    <loc>${escapeXml(entry.loc)}</loc>`,
    `    <changefreq>${escapeXml(entry.changefreq)}</changefreq>`,
    `    <priority>${escapeXml(entry.priority)}</priority>`,
    "  </url>",
  ].join("\n");
}

export function sitemapXml(entries: SitemapEntry[]): string {
  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...entries.map(url),
    "</urlset>",
    "",
  ].join("\n");
}

export function robotsTxt(siteUrl: string): string {
  return ["User-agent: *", "Allow: /", "", `Sitemap: ${siteUrl}/sitemap.xml`, ""].join("\n");
}
