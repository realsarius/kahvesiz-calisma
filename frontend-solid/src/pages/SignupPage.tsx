import { A, useNavigate } from "@solidjs/router";
import { Show, createSignal } from "solid-js";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { PageContainer } from "../components/ui/PageContainer";
import { ApiRequestError, apiPost } from "../lib/api";

interface SignupResponse {
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

export default function SignupPage() {
  const navigate = useNavigate();

  const [name, setName] = createSignal("");
  const [email, setEmail] = createSignal("");
  const [password, setPassword] = createSignal("");
  const [passwordConfirm, setPasswordConfirm] = createSignal("");
  const [submitting, setSubmitting] = createSignal(false);
  const [errorMessage, setErrorMessage] = createSignal<string | null>(null);
  const [successMessage, setSuccessMessage] = createSignal<string | null>(null);

  const onSubmit = async (event: SubmitEvent) => {
    event.preventDefault();

    const cleanName = name().trim();
    const cleanEmail = email().trim();

    if (!cleanName || !cleanEmail || !password().trim()) {
      setErrorMessage("Tüm alanlar zorunludur.");
      setSuccessMessage(null);
      return;
    }

    if (password().length < 8) {
      setErrorMessage("Şifre en az 8 karakter olmalı.");
      setSuccessMessage(null);
      return;
    }

    if (password() !== passwordConfirm()) {
      setErrorMessage("Şifre tekrar alanı eşleşmiyor.");
      setSuccessMessage(null);
      return;
    }

    setSubmitting(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const response = await apiPost<SignupResponse>(
        "/api/signup",
        {
          name: cleanName,
          email: cleanEmail,
          password: password(),
        },
        {
          retries: 0,
          timeoutMs: 12_000,
          emitAuthEvent: false,
        },
      );

      setSuccessMessage(response?.message || "Kayıt başarıyla tamamlandı.");
      setName("");
      setEmail("");
      setPassword("");
      setPasswordConfirm("");
    } catch (error) {
      setErrorMessage(toErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PageContainer title="Kayıt ol" subtitle="Session + CSRF uyumlu kayıt akışı">
      <Card>
        <Show when={errorMessage()}>
          {(value) => <Alert variant="error">{value()}</Alert>}
        </Show>

        <Show when={successMessage()}>
          {(value) => (
            <Alert variant="success" title="Kayıt tamamlandı">
              {value()}
            </Alert>
          )}
        </Show>

        <form class="stack-form" onSubmit={onSubmit}>
          <Input
            id="signup-name"
            type="text"
            label="İsim"
            value={name()}
            onInput={(event) => setName(event.currentTarget.value)}
            placeholder="Ad Soyad"
          />

          <Input
            id="signup-email"
            type="email"
            label="E-posta"
            value={email()}
            onInput={(event) => setEmail(event.currentTarget.value)}
            placeholder="ornek@alan.com"
          />

          <Input
            id="signup-password"
            type="password"
            label="Şifre"
            value={password()}
            onInput={(event) => setPassword(event.currentTarget.value)}
            placeholder="En az 8 karakter"
          />

          <Input
            id="signup-password-confirm"
            type="password"
            label="Şifre tekrar"
            value={passwordConfirm()}
            onInput={(event) => setPasswordConfirm(event.currentTarget.value)}
            placeholder="Şifrenizi tekrar girin"
          />

          <div class="row-actions">
            <Button type="submit" disabled={submitting()}>
              {submitting() ? "Kayıt yapılıyor..." : "Kayıt ol"}
            </Button>
            <Button type="button" variant="secondary" onClick={() => void navigate("/login?signup=ok")}>
              Giriş sayfasına git
            </Button>
          </div>
        </form>

        <p class="paragraph paragraph--compact">
          Zaten hesabın var mı? <A class="ui-link" href="/login">Giriş yap</A>
        </p>
      </Card>
    </PageContainer>
  );
}
