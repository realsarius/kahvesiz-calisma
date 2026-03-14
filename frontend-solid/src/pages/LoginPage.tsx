import { A, useLocation, useNavigate } from "@solidjs/router";
import { Show, createMemo, createSignal } from "solid-js";
import { useAuth } from "../auth/AuthContext";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { PageContainer } from "../components/ui/PageContainer";
import { ApiRequestError, apiPost } from "../lib/api";

interface LoginResponse {
  message?: string;
}

interface MagicLinkResponse {
  message?: string;
  debug_token?: string | null;
}

function toErrorMessage(error: unknown) {
  if (error instanceof ApiRequestError) {
    if (error.code === "REQUEST_TIMEOUT") {
      return "İstek zaman aşımına uğradı. Lütfen tekrar deneyin.";
    }

    if (error.code === "NETWORK_ERROR") {
      return "Sunucuya bağlanılamadı. Ağ bağlantınızı kontrol edin.";
    }

    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Beklenmeyen bir hata oluştu.";
}

function sanitizeRedirect(raw: string | null) {
  if (!raw) {
    return "/";
  }

  if (!raw.startsWith("/") || raw.startsWith("//")) {
    return "/";
  }

  return raw;
}

export default function LoginPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const auth = useAuth();

  const [email, setEmail] = createSignal("");
  const [password, setPassword] = createSignal("");
  const [submitting, setSubmitting] = createSignal(false);
  const [magicLinkSubmitting, setMagicLinkSubmitting] = createSignal(false);
  const [errorMessage, setErrorMessage] = createSignal<string | null>(null);
  const [magicLinkMessage, setMagicLinkMessage] = createSignal<string | null>(null);
  const [debugMagicLinkToken, setDebugMagicLinkToken] = createSignal<string | null>(null);

  const reason = createMemo(() => new URLSearchParams(location.search).get("reason"));
  const redirectTarget = createMemo(() => sanitizeRedirect(new URLSearchParams(location.search).get("redirect")));
  const signedUp = createMemo(() => new URLSearchParams(location.search).get("signup") === "ok");

  const onSubmit = async (event: SubmitEvent) => {
    event.preventDefault();

    if (!email().trim() || !password().trim()) {
      setErrorMessage("E-posta ve şifre alanları zorunludur.");
      return;
    }

    setSubmitting(true);
    setErrorMessage(null);
    setMagicLinkMessage(null);
    setDebugMagicLinkToken(null);

    try {
      await apiPost<LoginResponse>(
        "/api/login",
        {
          email: email().trim(),
          password: password(),
        },
        {
          retries: 0,
          timeoutMs: 10_000,
          emitAuthEvent: false,
        },
      );

      // Create a FastAPI session so admin endpoints work.
      try {
        await apiPost("/api/v1/auth/bridge-session", {}, {
          retries: 0,
          timeoutMs: 5_000,
          includeCsrf: false,
          emitAuthEvent: false,
        });
      } catch {
        // Bridge failure is non-blocking; legacy session still works.
        console.warn("FastAPI bridge-session oluşturulamadı.");
      }

      await auth.bootstrap();
      void navigate(redirectTarget(), { replace: true });
    } catch (error) {
      setErrorMessage(toErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  const requestMagicLink = async () => {
    const cleanEmail = email().trim();
    if (!cleanEmail) {
      setErrorMessage("Magic link göndermek için e-posta alanını doldurun.");
      return;
    }

    setMagicLinkSubmitting(true);
    setErrorMessage(null);
    setMagicLinkMessage(null);
    setDebugMagicLinkToken(null);

    try {
      const response = await apiPost<MagicLinkResponse>(
        "/api/v1/auth/magic-link",
        { email: cleanEmail },
        {
          retries: 0,
          timeoutMs: 10_000,
          emitAuthEvent: false,
        },
      );
      setMagicLinkMessage(response?.message || "Magic link gönderildi.");
      setDebugMagicLinkToken(response?.debug_token || null);
    } catch (error) {
      setErrorMessage(toErrorMessage(error));
    } finally {
      setMagicLinkSubmitting(false);
    }
  };

  return (
    <PageContainer title="Giriş" subtitle="Şifresiz (magic link) ve legacy şifreli giriş aynı ekranda sunulur.">
      <Card>
        <Show when={reason() === "session_expired"}>
          <Alert variant="warning" title="Oturum süresi doldu">
            Lütfen tekrar giriş yapın.
          </Alert>
        </Show>

        <Show when={signedUp()}>
          <Alert variant="success" title="Kayıt tamamlandı">
            Hesabınız oluşturuldu. E-posta doğrulamasından sonra giriş yapabilirsiniz.
          </Alert>
        </Show>

        <Show when={errorMessage()}>
          {(value) => <Alert variant="error">{value()}</Alert>}
        </Show>

        <Show when={magicLinkMessage()}>
          {(value) => (
            <Alert variant="success" title="Magic link gönderildi">
              {value()}
            </Alert>
          )}
        </Show>

        <Show when={debugMagicLinkToken()}>
          {(value) => (
            <Alert variant="warning" title="Geliştirme kısayolu">
              E-posta yerine doğrudan test etmek için{" "}
              <A
                class="ui-link"
                href={`/auth/verify?token=${encodeURIComponent(value())}&redirect=${encodeURIComponent(redirectTarget())}`}
              >
                bu doğrulama bağlantısını
              </A>{" "}
              kullanabilirsiniz.
            </Alert>
          )}
        </Show>

        <form class="stack-form" onSubmit={onSubmit}>
          <Input
            id="login-email"
            type="email"
            label="E-posta"
            value={email()}
            onInput={(event) => setEmail(event.currentTarget.value)}
            placeholder="ornek@alan.com"
          />

          <Input
            id="login-password"
            type="password"
            label="Şifre (legacy)"
            value={password()}
            onInput={(event) => setPassword(event.currentTarget.value)}
            placeholder="Şifreniz"
          />

          <div class="row-actions">
            <Button type="submit" disabled={submitting() || magicLinkSubmitting()}>
              {submitting() ? "Giriş yapılıyor..." : "Şifre ile giriş yap"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => void requestMagicLink()}
              disabled={magicLinkSubmitting() || submitting()}
            >
              {magicLinkSubmitting() ? "Link gönderiliyor..." : "Magic link gönder"}
            </Button>
          </div>
        </form>

        <p class="paragraph paragraph--compact">
          Hesabınız yok mu? <A class="ui-link" href="/signup">Kayıt olun</A>
        </p>
      </Card>
    </PageContainer>
  );
}
