const CSRF_META_SELECTOR = 'meta[name="csrf-token"]';
const CSRF_SOURCE_PATHS = ["/login", "/signup"];
const CSRF_ENDPOINT = "/api/csrf-token";

let cachedToken: string | null = null;

function readTokenFromMeta() {
  const meta = document.querySelector(CSRF_META_SELECTOR);
  const token = meta?.getAttribute("content")?.trim();
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

async function fetchTokenFromEndpoint() {
  try {
    const response = await fetch(CSRF_ENDPOINT, {
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
      data?: { csrf_token?: string };
    };

    const token = payload?.data?.csrf_token?.trim();
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

export function setCsrfToken(token: string | null) {
  cachedToken = token?.trim() || null;
}

export async function getCsrfToken(options: { forceRefresh?: boolean } = {}) {
  const forceRefresh = options.forceRefresh ?? false;

  if (!forceRefresh && cachedToken) {
    return cachedToken;
  }

  const metaToken = readTokenFromMeta();
  if (metaToken) {
    cachedToken = metaToken;
    return metaToken;
  }

  const endpointToken = await fetchTokenFromEndpoint();
  if (endpointToken) {
    cachedToken = endpointToken;
    return endpointToken;
  }

  const fetchedToken = await fetchTokenFromBackendPages();
  if (fetchedToken) {
    cachedToken = fetchedToken;
    return fetchedToken;
  }

  return null;
}
