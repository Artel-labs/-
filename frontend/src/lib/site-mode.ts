export const PRODUCTION = "production";
export const TEST = "test";
export const SITE_MODES = [PRODUCTION, TEST] as const;

export function demoClosed(mode: string): boolean {
  return mode === PRODUCTION;
}
