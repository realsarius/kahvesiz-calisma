import { A, useNavigate } from "@solidjs/router";
import { Show, createMemo, createSignal } from "solid-js";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { PageContainer } from "../components/ui/PageContainer";
import { ApiRequestError, apiPost } from "../lib/api";

interface RegisterResponse {
  message?: string;
  debug_email_verify_token?: string | null;
}

function toErrorMessage(error: unknown) {
  if (error instanceof ApiRequestError) {
    if (error.code === "REQUEST_TIMEOUT") {
      return "Istek zaman asimina ugradi. Lutfen tekrar deneyin.";
    }

    if (error.code === "NETWORK_ERROR") {
      return "Sunucuya baglanilamadi. Ag baglantinizi kontrol edin.";
    }

    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Beklenmeyen bir hata olustu.";
}

function normalizeUsername(raw: string) {
  return raw
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9._-]/g, "")
    .slice(0, 50);
}

export default function SignupPage() {
  const navigate = useNavigate();

  const [displayName, setDisplayName] = createSignal("");
  const [username, setUsername] = createSignal("");
  const [email, setEmail] = createSignal("");
  const [consentGiven, setConsentGiven] = createSignal(true);
  const [submitting, setSubmitting] = createSignal(false);
  const [errorMessage, setErrorMessage] = createSignal<string | null>(null);
  const [successMessage, setSuccessMessage] = createSignal<string | null>(null);
  const [debugVerifyToken, setDebugVerifyToken] = createSignal<string | null>(null);

  const verifyHref = createMemo(() => {
    const token = debugVerifyToken();
    if (!token) {
      return "";
    }
    return `/auth/email-verify?token=${encodeURIComponent(token)}`;
  });

  const onSubmit = async (event: SubmitEvent) => {
    event.preventDefault();

    const cleanDisplayName = displayName().trim();
    const cleanEmail = email().trim();
    const cleanUsername = normalizeUsername(username());

    if (!cleanDisplayName || !cleanEmail || !cleanUsername) {
      setErrorMessage("Isim, kullanici adi ve e-posta alanlari zorunludur.");
      setSuccessMessage(null);
      setDebugVerifyToken(null);
      return;
    }

    if (cleanUsername.length < 3) {
      setErrorMessage("Kullanici adi en az 3 karakter olmali.");
      setSuccessMessage(null);
      setDebugVerifyToken(null);
      return;
    }

    if (!consentGiven()) {
      setErrorMessage("Kayit icin KVKK onayi zorunludur.");
      setSuccessMessage(null);
      setDebugVerifyToken(null);
      return;
    }

    setSubmitting(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    setDebugVerifyToken(null);

    try {
      const response = await apiPost<RegisterResponse>(
        "/api/v1/auth/register",
        {
          email: cleanEmail,
          username: cleanUsername,
          display_name: cleanDisplayName,
          full_name: cleanDisplayName,
          consent_given: true,
          consent_version: "v1",
        },
        {
          retries: 0,
          timeoutMs: 12_000,
          emitAuthEvent: false,
        },
      );

      setSuccessMessage(
        response?.message || "Kayit basarili. E-posta dogrulama baglantisiyla giris yapabilirsiniz.",
      );
      setDebugVerifyToken(response?.debug_email_verify_token || null);
      setDisplayName("");
      setUsername("");
      setEmail("");
      setConsentGiven(true);
    } catch (error) {
      setErrorMessage(toErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PageContainer title="Kayit ol" subtitle="FastAPI magic-link uyumlu kayit akisi">
      <Card>
        <Show when={errorMessage()}>
          {(value) => <Alert variant="error">{value()}</Alert>}
        </Show>

        <Show when={successMessage()}>
          {(value) => (
            <Alert variant="success" title="Kayit tamamlandi">
              {value()}
            </Alert>
          )}
        </Show>

        <Show when={debugVerifyToken()}>
          {(value) => (
            <Alert variant="warning" title="Gelistirme kisayolu">
              E-posta beklemeden dogrulamayi test etmek icin{" "}
              <A class="ui-link" href={verifyHref()}>
                bu baglantiyi kullanin
              </A>
              . Token: <code>{value()}</code>
            </Alert>
          )}
        </Show>

        <form class="stack-form" onSubmit={onSubmit}>
          <Input
            id="signup-name"
            type="text"
            label="Gorunen isim"
            value={displayName()}
            onInput={(event) => setDisplayName(event.currentTarget.value)}
            placeholder="Ad Soyad"
          />

          <Input
            id="signup-username"
            type="text"
            label="Kullanici adi"
            value={username()}
            onInput={(event) => setUsername(event.currentTarget.value)}
            placeholder="ornek.kullanici"
            hint="3-50 karakter, kucuk harf / rakam / . _ -"
          />

          <Input
            id="signup-email"
            type="email"
            label="E-posta"
            value={email()}
            onInput={(event) => setEmail(event.currentTarget.value)}
            placeholder="ornek@alan.com"
          />

          <label class="flag-item" for="signup-consent">
            <input
              id="signup-consent"
              type="checkbox"
              checked={consentGiven()}
              onChange={(event) => setConsentGiven(event.currentTarget.checked)}
            />
            KVKK metnini okudum ve onayliyorum.
          </label>

          <div class="row-actions">
            <Button type="submit" disabled={submitting()}>
              {submitting() ? "Kayit yapiliyor..." : "Kayit ol"}
            </Button>
            <Button type="button" variant="secondary" onClick={() => void navigate("/login")}>
              Giris sayfasina git
            </Button>
          </div>
        </form>

        <p class="paragraph paragraph--compact">
          Zaten hesabin var mi? <A class="ui-link" href="/login">Giris yap</A>
        </p>
      </Card>
    </PageContainer>
  );
}
