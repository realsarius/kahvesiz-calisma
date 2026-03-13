import { Show, createMemo, createSignal } from "solid-js";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { PageContainer } from "../components/ui/PageContainer";
import { ApiRequestError } from "../lib/api";
import { sendContactMessage } from "../lib/contact";

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

export default function ContactPage() {
  const [email, setEmail] = createSignal("");
  const [subject, setSubject] = createSignal("");
  const [message, setMessage] = createSignal("");
  const [isSubmitted, setIsSubmitted] = createSignal(false);
  const [submitting, setSubmitting] = createSignal(false);
  const [submitError, setSubmitError] = createSignal<string | null>(null);

  const canSubmit = createMemo(() => {
    return email().trim().length > 3 && subject().trim().length > 2 && message().trim().length > 8;
  });

  const onSubmit = async (event: SubmitEvent) => {
    event.preventDefault();

    if (!canSubmit()) {
      setSubmitError("Lütfen tüm alanları doldurun.");
      setIsSubmitted(false);
      return;
    }

    setSubmitting(true);
    setSubmitError(null);

    try {
      await sendContactMessage({
        email: email().trim(),
        subject: subject().trim(),
        message: message().trim(),
      });

      setEmail("");
      setSubject("");
      setMessage("");
      setIsSubmitted(true);
    } catch (error) {
      setIsSubmitted(false);
      setSubmitError(toErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PageContainer title="İletişim" subtitle="Geri bildirim, hata raporu ve öneriler için iletişim formu.">
      <div class="grid-two-columns">
        <Card title="İletişim notları">
          <ul class="simple-list">
            <li>Konu: Teknik destek / İçerik düzeltme / Genel öneri</li>
            <li>Cevap süresi: Müsaitlik durumuna göre</li>
            <li>Ek bilgiler: Footer linklerinden gizlilik ve lisans sayfalarına ulaşabilirsiniz.</li>
          </ul>
        </Card>

        <Card title="Mesaj gönder">
          <Show when={isSubmitted()}>
            <Alert variant="success" title="Mesaj alındı">
              Mesajınız başarıyla iletildi.
            </Alert>
          </Show>

          <Show when={submitError()}>
            {(value) => <Alert variant="error">{value()}</Alert>}
          </Show>

          <form class="stack-form" onSubmit={onSubmit}>
            <Input
              id="contact-email"
              type="email"
              label="E-posta"
              value={email()}
              onInput={(event) => setEmail(event.currentTarget.value)}
              placeholder="ornek@alan.com"
            />

            <Input
              id="contact-subject"
              type="text"
              label="Konu"
              value={subject()}
              onInput={(event) => setSubject(event.currentTarget.value)}
              placeholder="Kısa konu"
            />

            <div class="ui-field">
              <label class="ui-field__label" for="contact-message">
                Mesaj
              </label>
              <textarea
                id="contact-message"
                class="ui-input ui-textarea"
                value={message()}
                onInput={(event) => setMessage(event.currentTarget.value)}
                placeholder="Mesajınızı buraya yazın"
              />
            </div>

            <Button type="submit" disabled={submitting()}>
              {submitting() ? "Gönderiliyor..." : "Mesajı gönder"}
            </Button>
          </form>
        </Card>
      </div>
    </PageContainer>
  );
}
