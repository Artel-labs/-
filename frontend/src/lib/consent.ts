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
const ADS_CONSENT_PATH = "/applications/ads-consent";
const NOT_FOUND = 404;

async function fetchText(path: string): Promise<Consent> {
  const consent = await fetchOptional<Consent>(path);
  if (consent === null) {
    throw new ApiError(path, NOT_FOUND);
  }
  return consent;
}

export function fetchConsent(): Promise<Consent> {
  return fetchText(CONSENT_PATH);
}

export function fetchAdsConsent(): Promise<Consent> {
  return fetchText(ADS_CONSENT_PATH);
}
