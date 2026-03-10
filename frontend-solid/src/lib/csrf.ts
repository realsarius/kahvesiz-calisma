const CSRF_META_SELECTOR = 'meta[name="csrf-token"]';
const CSRF_SOURCE_PATHS = ["/login", "/signup"];

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

  const fetchedToken = await fetchTokenFromBackendPages();
  if (fetchedToken) {
    cachedToken = fetchedToken;
    return fetchedToken;
  }

  return null;
}
