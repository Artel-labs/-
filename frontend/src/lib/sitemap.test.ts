import assert from "node:assert/strict";
import { test } from "node:test";

import { robotsTxt, sitemapXml } from "./sitemap.ts";

test("карта сайта перечисляет адреса с частотой и приоритетом", () => {
  const xml = sitemapXml([{ loc: "https://example.com/", changefreq: "monthly", priority: "1.0" }]);
  assert.equal(
    xml,
    [
      '<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
      "  <url>",
      "    <loc>https://example.com/</loc>",
      "    <changefreq>monthly</changefreq>",
      "    <priority>1.0</priority>",
      "  </url>",
      "</urlset>",
      "",
    ].join("\n"),
  );
});

test("адрес в карте сайта экранируется", () => {
  const xml = sitemapXml([{ loc: "https://example.com/?a=1&b=<2>", changefreq: "weekly", priority: "0.7" }]);
  assert.match(xml, /<loc>https:\/\/example\.com\/\?a=1&amp;b=&lt;2&gt;<\/loc>/);
});

test("robots.txt разрешает всё и указывает карту сайта", () => {
  assert.equal(robotsTxt("https://example.com"), "User-agent: *\nAllow: /\n\nSitemap: https://example.com/sitemap.xml\n");
});
