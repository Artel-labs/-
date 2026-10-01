import type { APIRoute } from "astro";

import { fetchSitemap } from "../lib/site";
import { sitemapXml } from "../lib/sitemap";

export const GET: APIRoute = async () =>
  new Response(sitemapXml(await fetchSitemap()), {
    headers: { "Content-Type": "application/xml; charset=utf-8" },
  });
