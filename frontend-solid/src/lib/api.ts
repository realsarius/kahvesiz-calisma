import { getCsrfToken } from "./csrf";

export const AUTH_REQUIRED_EVENT = "kahvesiz:auth-required";

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

interface ApiEnvelope<T> {
  data: T | null;
  error: ApiErrorPayload | null;
  meta: Record<string, unknown>;
}

interface ApiErrorPayload {
  message: string;
  code?: string;
  details?: unknown;
}

export interface ApiRequestOptions {
  method?: HttpMethod;
  headers?: HeadersInit;
  body?: unknown;
  timeoutMs?: number;
  retries?: number;
  includeCsrf?: boolean;
  emitAuthEvent?: boolean;
}

export class ApiRequestError extends Error {
  status: number;
  code: string | null;
  details: unknown;

  constructor(message: string, status: number, code: string | null = null, details: unknown = null) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

const DEFAULT_TIMEOUT_MS = 10_000;
const DEFAULT_GET_RETRIES = 2;

function sleep(durationMs: number) {
  return new Promise((resolve) => {
    setTimeout(resolve, durationMs);
  });
}

function isApiEnvelope<T>(payload: unknown): payload is ApiEnvelope<T> {
  if (!payload || typeof payload !== "object") {
    return false;
  }

  const candidate = payload as Record<string, unknown>;
  return "data" in candidate && "error" in candidate && "meta" in candidate;
}

function canHaveBody(method: HttpMethod) {
  return method !== "GET";
}

function toApiError(status: number, responsePayload: unknown, fallbackMessage: string) {
  if (isApiEnvelope<unknown>(responsePayload) && responsePayload.error) {
    const errorPayload = responsePayload.error;
    return new ApiRequestError(
      errorPayload.message || fallbackMessage,
      status,
      errorPayload.code || null,
      errorPayload.details,
    );
  }

  return new ApiRequestError(fallbackMessage, status);
}

async function parseResponse(response: Response) {
  const text = await response.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text) as unknown;
  } catch {
    return null;
  }
}

function notifyAuthRequired() {
  window.dispatchEvent(new CustomEvent(AUTH_REQUIRED_EVENT));
}

function shouldRetry(method: HttpMethod, attempt: number, maxAttempts: number, error: unknown) {
  if (method !== "GET" || attempt >= maxAttempts - 1) {
    return false;
  }

  if (error instanceof ApiRequestError) {
    return error.status >= 500;
  }

  if (error instanceof DOMException && error.name === "AbortError") {
    return true;
  }

  return error instanceof TypeError;
}

export async function apiRequest<T>(url: string, options: ApiRequestOptions = {}) {
  const method = options.method ?? "GET";
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const retries = method === "GET" ? options.retries ?? DEFAULT_GET_RETRIES : 0;
  const includeCsrf = options.includeCsrf ?? canHaveBody(method);
  const emitAuthEvent = options.emitAuthEvent ?? true;
  const maxAttempts = retries + 1;

  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const headers = new Headers(options.headers);
      headers.set("Accept", "application/json");

      let body: BodyInit | undefined;
      if (canHaveBody(method) && options.body !== undefined) {
        headers.set("Content-Type", "application/json");
        body = JSON.stringify(options.body);
      }

      if (includeCsrf) {
        const csrfToken = await getCsrfToken();
        if (!csrfToken) {
          throw new ApiRequestError(
            "CSRF token bulunamadi. Yazma istegi guvenli sekilde reddedildi.",
            419,
            "CSRF_TOKEN_MISSING",
          );
        }
        headers.set("X-CSRFToken", csrfToken);
      }

      const response = await fetch(url, {
        method,
        credentials: "include",
        headers,
        body,
        signal: controller.signal,
      });

      const payload = await parseResponse(response);

      if (!response.ok) {
        const apiError = toApiError(response.status, payload, `HTTP ${response.status} hatasi.`);
        if (apiError.status === 401 && emitAuthEvent) {
          notifyAuthRequired();
        }
        throw apiError;
      }

      if (isApiEnvelope<T>(payload)) {
        if (payload.error) {
          throw new ApiRequestError(
            payload.error.message || "API hatasi olustu.",
            response.status,
            payload.error.code || null,
            payload.error.details,
          );
        }

        return payload.data as T;
      }

      return payload as T;
    } catch (error) {
      if (shouldRetry(method, attempt, maxAttempts, error)) {
        await sleep(150 * (attempt + 1));
        continue;
      }

      if (error instanceof ApiRequestError) {
        throw error;
      }

      if (error instanceof DOMException && error.name === "AbortError") {
        throw new ApiRequestError("Istek zaman asimina ugradi.", 408, "REQUEST_TIMEOUT");
      }

      throw new ApiRequestError("Ag hatasi olustu.", 0, "NETWORK_ERROR", error);
    } finally {
      clearTimeout(timeoutId);
    }
  }

  throw new ApiRequestError("Istek bilinmeyen bir nedenle tamamlanamadi.", 500);
}

export function apiGet<T>(url: string, options: Omit<ApiRequestOptions, "method" | "body"> = {}) {
  return apiRequest<T>(url, {
    ...options,
    method: "GET",
    includeCsrf: false,
  });
}

export function apiPost<T>(url: string, body: unknown, options: Omit<ApiRequestOptions, "method" | "body"> = {}) {
  return apiRequest<T>(url, {
    ...options,
    method: "POST",
    body,
  });
}

export function apiPut<T>(url: string, body: unknown, options: Omit<ApiRequestOptions, "method" | "body"> = {}) {
  return apiRequest<T>(url, {
    ...options,
    method: "PUT",
    body,
  });
}

export function apiDelete<T>(url: string, options: Omit<ApiRequestOptions, "method"> = {}) {
  return apiRequest<T>(url, {
    ...options,
    method: "DELETE",
  });
}
