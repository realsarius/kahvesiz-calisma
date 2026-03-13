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
  const [errorMessage, setErrorMessage] = createSignal<string | null>(null);

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

      await auth.bootstrap();
      void navigate(redirectTarget(), { replace: true });
    } catch (error) {
      setErrorMessage(toErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PageContainer title="Giriş" subtitle="Session + CSRF uyumlu giriş akışı">
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
            label="Şifre"
            value={password()}
            onInput={(event) => setPassword(event.currentTarget.value)}
            placeholder="Şifreniz"
          />

          <Button type="submit" disabled={submitting()}>
            {submitting() ? "Giriş yapılıyor..." : "Giriş yap"}
          </Button>
        </form>

        <p class="paragraph paragraph--compact">
          Hesabınız yok mu? <A class="ui-link" href="/signup">Kayıt olun</A>
        </p>
      </Card>
    </PageContainer>
  );
}
