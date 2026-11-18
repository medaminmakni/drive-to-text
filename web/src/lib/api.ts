// Every call to the backend goes through here, typed with the shapes of docs/API.md.

import type { Batch, BatchRequest, Config, FolderListing } from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError("Cannot reach the server. Is the backend running?", 0);
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    // The backend sends {"detail": "message"}. Validation errors (422) send a list instead.
    const detail = typeof body?.detail === "string" ? body.detail : `Request failed (${response.status}).`;
    throw new ApiError(detail, response.status);
  }
  return body as T;
}

export const api = {
  config: () => request<Config>("/api/config"),
  listFolder: (url: string) =>
    request<FolderListing>("/api/folders", { method: "POST", body: JSON.stringify({ url }) }),
  startBatch: (batch: BatchRequest) =>
    request<Batch>("/api/batches", { method: "POST", body: JSON.stringify(batch) }),
  getBatch: (id: string) => request<Batch>(`/api/batches/${encodeURIComponent(id)}`),
  exportUrl: (id: string) => `/api/batches/${encodeURIComponent(id)}/export`,
};

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong.";
}
