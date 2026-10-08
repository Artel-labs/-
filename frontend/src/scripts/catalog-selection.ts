export const ALL = "all";
export const VALUE_SEPARATOR = ",";

export function parseValues(raw: string | null, allowed: readonly string[]): string[] {
  if (!raw) {
    return [];
  }
  const wanted = raw.split(VALUE_SEPARATOR).map((value) => value.trim());
  return allowed.filter((value) => value !== ALL && wanted.includes(value));
}

export function passes(selected: readonly string[], value: string | undefined): boolean {
  return selected.length === 0 || (value !== undefined && selected.includes(value));
}

export function without(selected: readonly string[], value: string): string[] {
  return selected.filter((item) => item !== value);
}
