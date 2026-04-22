import { publicEnv } from "@/lib/config/env";
import { getSupabaseBrowserClient } from "@/lib/supabase/client";

export interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  meta?: Record<string, unknown>;
}

interface ApiErrorEnvelope {
  success: false;
  error?: {
    code?: string;
    message?: string;
    details?: Record<string, unknown>;
  };
  meta?: Record<string, unknown>;
}

export class ApiError extends Error {
  code: string;
  status: number;
  details?: Record<string, unknown>;

  constructor(message: string, code = "UNKNOWN_ERROR", status = 500, details?: Record<string, unknown>) {
    super(message);
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

async function getAuthorizationHeader(): Promise<string | null> {
  const supabase = getSupabaseBrowserClient();

  if (!supabase) {
    return null;
  }

  const {
    data: { session },
  } = await supabase.auth.getSession();

  return session?.access_token ? `Bearer ${session.access_token}` : null;
}

async function buildHeaders(init?: RequestInit): Promise<Headers> {
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");

  if (!headers.has("Authorization")) {
    const authorizationHeader = await getAuthorizationHeader();

    if (authorizationHeader) {
      headers.set("Authorization", authorizationHeader);
    }
  }

  return headers;
}

interface RequestOptions extends RequestInit {
  skipEnvelope?: boolean;
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  options?: RequestOptions
): Promise<T | undefined> {
  const headers = await buildHeaders(options);
  
  const init: RequestInit = {
    ...options,
    method,
    headers,
    cache: "no-store",
  };

  if (body !== undefined) {
    init.body = JSON.stringify(body);
  }

  const response = await fetch(`${publicEnv.NEXT_PUBLIC_API_BASE_URL}${path}`, init);

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined;
  }

  // Handle CSV/file responses (skip envelope parsing)
  const contentType = response.headers.get("content-type") ?? "";
  if (options?.skipEnvelope || contentType.includes("text/csv") || contentType.includes("application/octet-stream")) {
    if (!response.ok) {
      let message = `Request failed with status ${response.status}`;
      let code = "UNKNOWN_ERROR";

      if (contentType.includes("application/json")) {
        const errorPayload = (await response.json()) as ApiErrorEnvelope;
        message = errorPayload.error?.message ?? message;
        code = errorPayload.error?.code ?? code;
      }

      throw new ApiError(message, code, response.status);
    }

    return (await response.blob()) as unknown as T;
  }

  // Handle regular JSON envelope responses
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    let code = "UNKNOWN_ERROR";
    let details: Record<string, unknown> | undefined;

    if (contentType.includes("application/json")) {
      const errorPayload = (await response.json()) as ApiErrorEnvelope;
      message = errorPayload.error?.message ?? message;
      code = errorPayload.error?.code ?? code;
      details = errorPayload.error?.details;
    }

    throw new ApiError(message, code, response.status, details);
  }

  const payload = (await response.json()) as ApiEnvelope<T>;

  if (!payload.success) {
    throw new ApiError("API returned an unsuccessful response", "UNSUCCESSFUL_RESPONSE", response.status);
  }

  return payload.data;
}

export async function apiGet<T>(path: string, init?: RequestOptions): Promise<T> {
  const result = await request<T>("GET", path, undefined, init);
  return result as T;
}

export async function apiPost<T>(path: string, body?: unknown, init?: RequestInit): Promise<T> {
  const result = await request<T>("POST", path, body, init);
  return result as T;
}

export async function apiPatch<T>(path: string, body?: unknown, init?: RequestInit): Promise<T | undefined> {
  return request<T>("PATCH", path, body, init);
}

export async function apiDelete<T = void>(path: string, init?: RequestInit): Promise<T | undefined> {
  return request<T>("DELETE", path, undefined, init);
}
