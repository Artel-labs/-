import { ApiError, fetchOptional } from "./api";

export interface Consent {
  title: string;
  version: string;
  source: string;
  paragraphs: string[];
  withdraw_text: string;
  withdraw_url: string;
}

const CONSENT_PATH = "/applications/consent";
const NOT_FOUND = 404;

export async function fetchConsent(): Promise<Consent> {
  const consent = await fetchOptional<Consent>(CONSENT_PATH);
  if (consent === null) {
    throw new ApiError(CONSENT_PATH, NOT_FOUND);
  }
  return consent;
}
