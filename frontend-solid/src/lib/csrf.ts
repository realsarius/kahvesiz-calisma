const CSRF_META_SELECTOR = 'meta[name="csrf-token"]';
const CSRF_SOURCE_PATHS = ["/login", "/signup"];
const CSRF_ENDPOINTS_BY_SCOPE = {
  fastapi: ["/api/v1/auth/csrf"],
  legacy: ["/api/csrf-token"],
} as const;
const CSRF_COOKIE_NAME = "csrf_token";

export type CsrfScope = "fastapi" | "legacy";

const cachedTokens: Record<CsrfScope, string | null> = {
  fastapi: null,
  legacy: null,
};

function readTokenFromMeta() {
  const meta = document.querySelector(CSRF_META_SELECTOR);
  const token = meta?.getAttribute("content")?.trim();
  return token || null;
}

function readTokenFromCookie() {
  const cookies = document.cookie.split(";").map((item) => item.trim());
  const prefix = `${CSRF_COOKIE_NAME}=`;
  const hit = cookies.find((item) => item.startsWith(prefix));
  if (!hit) {
    return null;
  }
  const token = decodeURIComponent(hit.slice(prefix.length)).trim();
  return token || null;
}

function extractTokenFromHtml(html: string) {
  const metaMatch = html.match(/<meta\s+name=["']csrf-token["']\s+content=["']([^"']+)["']/i);
  if (metaMatch?.[1]) {
    return metaMatch[1];
  }

  const inputMatch = html.match(/name=["']csrf_token["']\s+type=["']hidden["']\s+value=["']([^"']+)["']/i);
  if (inputMatch?.[1]) {
    return inputMatch[1];
  }

  return null;
}

async function fetchTokenFromEndpoint(path: string) {
  try {
    const response = await fetch(path, {
      method: "GET",
      credentials: "include",
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      return null;
    }

    const payload = (await response.json()) as {
      csrf_token?: string;
      data?: { csrf_token?: string };
    };

    const token = payload?.csrf_token?.trim() || payload?.data?.csrf_token?.trim();
    return token || null;
  } catch {
    return null;
  }
}

async function fetchTokenFromBackendPages() {
  for (const path of CSRF_SOURCE_PATHS) {
    try {
      const response = await fetch(path, {
        method: "GET",
        credentials: "include",
        headers: {
          Accept: "text/html",
        },
      });

      if (!response.ok) {
        continue;
      }

      const html = await response.text();
      const token = extractTokenFromHtml(html);
      if (token) {
        return token;
      }
    } catch {
      // CSRF token yoksa fail-open yerine yazma isteklerini API katmaninda fail-closed edecegiz.
    }
  }

  return null;
}

export function setCsrfToken(token: string | null, options: { scope?: CsrfScope } = {}) {
  const scope = options.scope ?? "fastapi";
  cachedTokens[scope] = token?.trim() || null;
}

export async function getCsrfToken(options: { forceRefresh?: boolean; scope?: CsrfScope } = {}) {
  const forceRefresh = options.forceRefresh ?? false;
  const scope = options.scope ?? "fastapi";

  if (!forceRefresh && cachedTokens[scope]) {
    return cachedTokens[scope];
  }

  if (scope === "legacy") {
    const metaToken = readTokenFromMeta();
    if (metaToken) {
      cachedTokens[scope] = metaToken;
      return metaToken;
    }
  }

  if (scope === "fastapi") {
    const cookieToken = readTokenFromCookie();
    if (cookieToken) {
      cachedTokens[scope] = cookieToken;
      return cookieToken;
    }
  }

  for (const endpoint of CSRF_ENDPOINTS_BY_SCOPE[scope]) {
    const endpointToken = await fetchTokenFromEndpoint(endpoint);
    if (endpointToken) {
      cachedTokens[scope] = endpointToken;
      return endpointToken;
    }
  }

  if (scope === "legacy") {
    const fetchedToken = await fetchTokenFromBackendPages();
    if (fetchedToken) {
      cachedTokens[scope] = fetchedToken;
      return fetchedToken;
    }
  }

  return null;
}
