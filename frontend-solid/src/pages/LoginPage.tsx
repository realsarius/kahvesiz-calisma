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
      setErrorMessage("E-posta ve sifre alanlari zorunludur.");
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
    <PageContainer title="Login" subtitle="Session + CSRF uyumlu login akisi">
      <Card>
        <Show when={reason() === "session_expired"}>
          <Alert variant="warning" title="Oturum suresi doldu">
            Lutfen tekrar login olun.
          </Alert>
        </Show>

        <Show when={signedUp()}>
          <Alert variant="success" title="Kayit tamamlandi">
            Hesabiniz olusturuldu. E-posta dogrulamasindan sonra login olabilirsiniz.
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
            label="Sifre"
            value={password()}
            onInput={(event) => setPassword(event.currentTarget.value)}
            placeholder="Sifreniz"
          />

          <Button type="submit" disabled={submitting()}>
            {submitting() ? "Giris yapiliyor..." : "Giris yap"}
          </Button>
        </form>

        <p class="paragraph paragraph--compact">
          Hesabiniz yok mu? <A class="ui-link" href="/signup">Kayit olun</A>
        </p>
      </Card>
    </PageContainer>
  );
}
