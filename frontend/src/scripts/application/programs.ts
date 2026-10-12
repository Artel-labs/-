import type { ProgramChoice } from "../../lib/hse-forms";
import { PROGRAMS_ENDPOINT } from "./constants";

let cached: Promise<ProgramChoice[]> | null = null;

export function loadPrograms(): Promise<ProgramChoice[]> {
  cached ??= fetch(PROGRAMS_ENDPOINT, { credentials: "omit" })
    .then((response) => (response.ok ? (response.json() as Promise<ProgramChoice[]>) : []))
    .catch(() => []);
  return cached;
}
