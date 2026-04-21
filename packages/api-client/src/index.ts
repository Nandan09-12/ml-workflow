export type ApiMeta = {
  requestId?: string;
  page?: number;
  pageSize?: number;
  total?: number;
};

export type ApiError = {
  code: string;
  message: string;
  details?: unknown;
};

export type ApiSuccessEnvelope<T> = {
  success: true;
  data: T;
  meta?: ApiMeta;
};

export type ApiErrorEnvelope = {
  success: false;
  error: ApiError;
  meta?: ApiMeta;
};

export type ApiEnvelope<T> = ApiSuccessEnvelope<T> | ApiErrorEnvelope;

export class ApiClientError extends Error {
  code: string;
  details?: unknown;
  status?: number;

  constructor(message: string, code = "UNKNOWN_ERROR", details?: unknown, status?: number) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.details = details;
    this.status = status;
  }
}

export type CreateApiClientOptions = {
  baseUrl: string;
  getAccessToken?: () => Promise<string | null> | string | null;
  requestTimeoutMs?: number;
};

type RequestOptions = RequestInit & {
  query?: Record<string, string | number | boolean | undefined>;
};

function buildUrl(baseUrl: string, path: string, query?: RequestOptions["query"]) {
  const url = new URL(path, baseUrl);

  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    });
  }

  return url.toString();
}

export function createApiClient(options: CreateApiClientOptions) {
  const request = async <T>(path: string, init: RequestOptions = {}): Promise<T> => {
    const token = await options.getAccessToken?.();
    const headers = new Headers(init.headers);
    const controller = new AbortController();
    const timeoutMs = options.requestTimeoutMs ?? 15000;
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    if (!headers.has("Content-Type") && !(init.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }

    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    let response: Response;
    try {
      response = await fetch(buildUrl(options.baseUrl, path, init.query), {
        ...init,
        headers,
        signal: init.signal ?? controller.signal,
      });
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof Error && error.name === "AbortError") {
        throw new ApiClientError("Request timed out", "REQUEST_TIMEOUT");
      }

      if (error instanceof Error) {
        throw new ApiClientError(
          "Unable to reach the backend. Check that the API is running and reachable from the app.",
          "NETWORK_REQUEST_FAILED",
          error.message,
        );
      }

      throw new ApiClientError(
        "Unable to reach the backend. Check that the API is running and reachable from the app.",
        "NETWORK_REQUEST_FAILED",
      );
    }

    clearTimeout(timeoutId);

    if (response.status === 204) {
      return undefined as T;
    }

    const rawBody = await response.text();
    let payload: ApiEnvelope<T> | null = null;

    if (rawBody) {
      try {
        payload = JSON.parse(rawBody) as ApiEnvelope<T>;
      } catch {
        if (!response.ok) {
          throw new ApiClientError(
            rawBody.trim() || "Request failed",
            "NON_JSON_ERROR_RESPONSE",
            { rawBody },
            response.status,
          );
        }

        throw new ApiClientError(
          "Backend returned an unexpected response format.",
          "INVALID_RESPONSE_FORMAT",
          { rawBody },
          response.status,
        );
      }
    }

    if (!payload) {
      throw new ApiClientError(
        "Backend returned an empty response.",
        "EMPTY_RESPONSE",
        undefined,
        response.status,
      );
    }

    if (!response.ok || payload.success === false) {
      const error = payload.success === false ? payload.error : undefined;
      throw new ApiClientError(
        error?.message ?? "Request failed",
        error?.code ?? "REQUEST_FAILED",
        error?.details,
        response.status,
      );
    }

    return payload.data;
  };

  return {
    get: <T>(path: string, init?: RequestOptions) =>
      request<T>(path, { ...init, method: "GET" }),
    post: <T>(path: string, body?: unknown, init?: RequestOptions) =>
      request<T>(path, {
        ...init,
        method: "POST",
        body: body instanceof FormData ? body : JSON.stringify(body ?? {}),
      }),
    patch: <T>(path: string, body?: unknown, init?: RequestOptions) =>
      request<T>(path, {
        ...init,
        method: "PATCH",
        body: body instanceof FormData ? body : JSON.stringify(body ?? {}),
      }),
  };
}
