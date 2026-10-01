import { fetchOptional } from "./api";
import type { ProgramPage } from "./program";

export function fetchProgramPage(hseId: string): Promise<ProgramPage | null> {
  return fetchOptional<ProgramPage>(`/catalog/programs/${encodeURIComponent(hseId)}`);
}
