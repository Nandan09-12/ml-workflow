import { publicEnv } from "@/lib/config/env";

export interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  meta?: Record<string, unknown>;
}

export class ApiError extends Error {
  code: string;

  constructor(message: string, code = "UNKNOWN_ERROR") {
    super(message);
    this.code = code;
  }
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${publicEnv.NEXT_PUBLIC_API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new ApiError(`Request failed with status ${response.status}`);
  }

  const payload = (await response.json()) as ApiEnvelope<T>;

  if (!payload.success) {
    throw new ApiError("API returned an unsuccessful response");
  }

  return payload.data;
}
