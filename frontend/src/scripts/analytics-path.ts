export const KEPT_PARAMS = ["utm_source", "utm_medium", "utm_campaign"];

export function keptQuery(search: string): string {
  const params = new URLSearchParams(search);
  const kept = new URLSearchParams();
  for (const key of KEPT_PARAMS) {
    const value = params.get(key);
    if (value) {
      kept.set(key, value);
    }
  }
  const query = kept.toString();
  return query ? `?${query}` : "";
}
