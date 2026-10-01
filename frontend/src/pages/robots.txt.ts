import type { APIRoute } from "astro";

import { fetchSite } from "../lib/site";
import { robotsTxt } from "../lib/sitemap";

export const GET: APIRoute = async () =>
  new Response(robotsTxt((await fetchSite()).site_url), {
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
