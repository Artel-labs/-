import { API_URL } from "astro:env/server";

const NOT_FOUND = 404;

export class ApiError extends Error {
  constructor(path: string, status: number) {
    super(`API ${path} ответил ${String(status)}`);
    this.name = "ApiError";
  }
}

export async function fetchOptional<T>(path: string): Promise<T | null> {
  const response = await fetch(`${API_URL}/api${path}`, { headers: { Accept: "application/json" } });
  if (response.status === NOT_FOUND) {
    return null;
  }
  if (!response.ok) {
    throw new ApiError(path, response.status);
  }
  return (await response.json()) as T;
}
