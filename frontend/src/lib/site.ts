import { ApiError, fetchOptional } from "./api";

export interface Site {
  site_url: string;
  image_url: string;
}

export interface SitemapEntry {
  loc: string;
  changefreq: string;
  priority: string;
}

const SITE_PATH = "/site";
const SITEMAP_PATH = "/catalog/sitemap";
const NOT_FOUND = 404;

async function fetchRequired<T>(path: string): Promise<T> {
  const data = await fetchOptional<T>(path);
  if (data === null) {
    throw new ApiError(path, NOT_FOUND);
  }
  return data;
}

export function fetchSite(): Promise<Site> {
  return fetchRequired<Site>(SITE_PATH);
}

export function fetchSitemap(): Promise<SitemapEntry[]> {
  return fetchRequired<SitemapEntry[]>(SITEMAP_PATH);
}
