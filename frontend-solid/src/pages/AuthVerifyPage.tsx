import { A, useLocation, useNavigate } from "@solidjs/router";
import { Show, createMemo, createSignal, onMount } from "solid-js";
import { useAuth } from "../auth/AuthContext";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { LoadingState } from "../components/states/LoadingState";
import { PageContainer } from "../components/ui/PageContainer";
import { ApiRequestError, apiGet } from "../lib/api";

interface VerifyAuthUser {
  id: string;
  email: string;
  username: string;
  display_name?: string | null;
  role?: string;
}

interface VerifyApiResponse {
  message?: string;
  user: VerifyAuthUser;
}

function sanitizeRedirect(raw: string | null) {
  if (!raw) {
    return "/cafes";
  }
  if (!raw.startsWith("/") || raw.startsWith("//")) {
    return "/cafes";
  }
  return raw;
}

function toErrorMessage(error: unknown) {
  if (error instanceof ApiRequestError) {
    if (error.code === "REQUEST_TIMEOUT") {
      return "Doğrulama isteği zaman aşımına uğradı. Tekrar deneyin.";
    }
    if (error.code === "NETWORK_ERROR") {
      return "Sunucuya bağlanılamadı. Ağ bağlantınızı kontrol edin.";
    }
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Bağlantı doğrulanamadı.";
}

export default function AuthVerifyPage() {
  const auth = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const [loading, setLoading] = createSignal(true);
  const [successMessage, setSuccessMessage] = createSignal<string | null>(null);
  const [errorMessage, setErrorMessage] = createSignal<string | null>(null);

  const token = createMemo(() => new URLSearchParams(location.search).get("token")?.trim() || "");
  const redirectTarget = createMemo(() => sanitizeRedirect(new URLSearchParams(location.search).get("redirect")));

  const runVerification = async () => {
    const plainToken = token();
    if (!plainToken) {
      setErrorMessage("Doğrulama bağlantısı geçersiz görünüyor. Token bulunamadı.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setSuccessMessage(null);
    setErrorMessage(null);

    try {
      const response = await apiGet<VerifyApiResponse>(
        `/api/v1/auth/verify?token=${encodeURIComponent(plainToken)}`,
        {
          retries: 0,
          timeoutMs: 12_000,
          emitAuthEvent: false,
        },
      );

      const user = response.user;
      auth.setUser({
        id: user.id,
        email: user.email,
        name: user.display_name || user.username || user.email,
        role: user.role || "user",
        isAdmin: user.role === "admin",
      });

      setSuccessMessage(response.message || "Doğrulama başarılı. Yönlendiriliyorsunuz...");
      setLoading(false);
      window.setTimeout(() => {
        void navigate(redirectTarget(), { replace: true });
      }, 700);
    } catch (error) {
      setErrorMessage(toErrorMessage(error));
      setLoading(false);
    }
  };

  onMount(() => {
    void runVerification();
  });

  return (
    <PageContainer title="Bağlantı Doğrulama" subtitle="Magic link ve email doğrulama bağlantıları burada işlenir.">
      <Show when={loading()} fallback={null}>
        <LoadingState title="Doğrulama yapılıyor" description="Bağlantı kontrol ediliyor, lütfen bekleyin." />
      </Show>

      <Show when={successMessage()}>
        {(value) => (
          <Card>
            <Alert variant="success" title="Başarılı">
              {value()}
            </Alert>
          </Card>
        )}
      </Show>

      <Show when={errorMessage()}>
        {(value) => (
          <Card>
            <Alert variant="error" title="Doğrulama başarısız">
              {value()}
            </Alert>
            <div class="row-actions">
              <Button type="button" onClick={() => void runVerification()}>
                Tekrar dene
              </Button>
              <Button type="button" variant="secondary" onClick={() => void navigate("/login", { replace: true })}>
                Giriş sayfasına git
              </Button>
            </div>
            <p class="paragraph paragraph--compact">
              Hesap oluşturmanız gerekiyorsa <A class="ui-link" href="/signup">kayıt sayfasına</A> geçebilirsiniz.
            </p>
          </Card>
        )}
      </Show>
    </PageContainer>
  );
}
