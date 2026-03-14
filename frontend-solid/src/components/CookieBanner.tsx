import { Show, createSignal, onMount } from "solid-js";
import { useAuth } from "../auth/AuthContext";
import { apiRequest } from "../lib/api";

const STORAGE_KEY = "kahvesiz_cookie_consent_v1";
const CONSENT_VERSION = "v1";

interface StoredConsent {
  consent_version: string;
  decided_at: string;
  analytics_allowed: boolean;
  marketing_allowed: boolean;
}

function readStoredConsent(): StoredConsent | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return null;
    }

    const parsed = JSON.parse(raw) as Partial<StoredConsent>;
    if (!parsed || typeof parsed !== "object") {
      return null;
    }

    if (typeof parsed.consent_version !== "string") {
      return null;
    }

    return {
      consent_version: parsed.consent_version,
      decided_at: typeof parsed.decided_at === "string" ? parsed.decided_at : "",
      analytics_allowed: Boolean(parsed.analytics_allowed),
      marketing_allowed: Boolean(parsed.marketing_allowed),
    };
  } catch {
    return null;
  }
}

function storeConsent(payload: StoredConsent) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  } catch {
    // no-op: storage unavailable
  }
}

export function CookieBanner() {
  const auth = useAuth();

  const [visible, setVisible] = createSignal(false);
  const [manageOpen, setManageOpen] = createSignal(false);
  const [analyticsAllowed, setAnalyticsAllowed] = createSignal(false);
  const [marketingAllowed, setMarketingAllowed] = createSignal(false);
  const [saving, setSaving] = createSignal(false);

  onMount(() => {
    const stored = readStoredConsent();
    if (!stored || stored.consent_version !== CONSENT_VERSION) {
      setVisible(true);
      return;
    }

    setAnalyticsAllowed(stored.analytics_allowed);
    setMarketingAllowed(stored.marketing_allowed);
  });

  const syncConsentToBackend = async (payload: StoredConsent) => {
    if (!auth.state.isAuthenticated) {
      return;
    }

    await apiRequest("/api/v1/users/me/consent", {
      method: "PATCH",
      body: {
        consent_version: payload.consent_version,
        analytics_allowed: payload.analytics_allowed,
        marketing_allowed: payload.marketing_allowed,
      },
      retries: 0,
      emitAuthEvent: false,
    });
  };

  const applyDecision = async (analytics: boolean, marketing: boolean) => {
    const payload: StoredConsent = {
      consent_version: CONSENT_VERSION,
      decided_at: new Date().toISOString(),
      analytics_allowed: analytics,
      marketing_allowed: marketing,
    };

    setSaving(true);
    setAnalyticsAllowed(analytics);
    setMarketingAllowed(marketing);
    storeConsent(payload);

    try {
      await syncConsentToBackend(payload);
      setVisible(false);
      setManageOpen(false);
    } catch {
      // Local consent remains source of truth for guests and temporary backend failures.
      setVisible(false);
      setManageOpen(false);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Show when={visible()}>
      <aside class="cookie-banner" role="dialog" aria-live="polite" aria-label="Çerez tercihleri">
        <p class="cookie-banner__text">
          Deneyimi iyileştirmek için zorunlu çerezleri kullanıyoruz. Analitik ve pazarlama çerezlerini tercihlerinize göre yönetebilirsiniz.
        </p>

        <div class="cookie-banner__actions">
          <button
            type="button"
            class="ui-button ui-button--secondary ui-button--sm"
            disabled={saving()}
            onClick={() => void applyDecision(false, false)}
          >
            Zorunlu olanlar
          </button>
          <button
            type="button"
            class="ui-button ui-button--secondary ui-button--sm"
            disabled={saving()}
            onClick={() => setManageOpen((value) => !value)}
          >
            Tercihleri yönet
          </button>
          <button
            type="button"
            class="ui-button ui-button--primary ui-button--sm"
            disabled={saving()}
            onClick={() => void applyDecision(true, true)}
          >
            Tümünü kabul et
          </button>
        </div>

        <Show when={manageOpen()}>
          <div class="cookie-banner__panel">
            <label class="flag-item">
              <input type="checkbox" checked disabled />
              Zorunlu çerezler (her zaman açık)
            </label>
            <label class="flag-item">
              <input
                type="checkbox"
                checked={analyticsAllowed()}
                onChange={(event) => setAnalyticsAllowed(event.currentTarget.checked)}
              />
              Analitik çerezler
            </label>
            <label class="flag-item">
              <input
                type="checkbox"
                checked={marketingAllowed()}
                onChange={(event) => setMarketingAllowed(event.currentTarget.checked)}
              />
              Pazarlama çerezleri
            </label>

            <button
              type="button"
              class="ui-button ui-button--primary ui-button--sm"
              disabled={saving()}
              onClick={() => void applyDecision(analyticsAllowed(), marketingAllowed())}
            >
              Tercihleri kaydet
            </button>
          </div>
        </Show>
      </aside>
    </Show>
  );
}
