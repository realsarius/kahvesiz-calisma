import { Show, createMemo, createSignal } from "solid-js";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { PageContainer } from "../components/ui/PageContainer";

export default function ContactPage() {
  const [email, setEmail] = createSignal("");
  const [subject, setSubject] = createSignal("");
  const [message, setMessage] = createSignal("");
  const [isSubmitted, setIsSubmitted] = createSignal(false);
  const [submitError, setSubmitError] = createSignal<string | null>(null);

  const canSubmit = createMemo(() => {
    return email().trim().length > 3 && subject().trim().length > 2 && message().trim().length > 8;
  });

  const onSubmit = (event: SubmitEvent) => {
    event.preventDefault();

    if (!canSubmit()) {
      setSubmitError("Lutfen tum alanlari doldurun.");
      setIsSubmitted(false);
      return;
    }

    setSubmitError(null);
    setIsSubmitted(true);
  };

  return (
    <PageContainer title="Iletisim" subtitle="Geri bildirim, hata raporu ve oneriler icin iletisim formu.">
      <div class="grid-two-columns">
        <Card title="Iletisim notlari">
          <ul class="simple-list">
            <li>Konu: Teknik destek / Icerik duzeltme / Genel oneri</li>
            <li>Cevap suresi: Musaitlik durumuna gore</li>
            <li>Ek bilgiler: Footer linklerinden gizlilik ve lisans sayfalarina ulasabilirsiniz.</li>
          </ul>
        </Card>

        <Card title="Mesaj gonder">
          <Show when={isSubmitted()}>
            <Alert variant="success" title="Mesaj alindi">
              Form alinmis gibi isaretlendi. Backend entegrasyonu bir sonraki adimda tamamlanacak.
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
              placeholder="Kisa konu"
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
                placeholder="Mesajinizi buraya yazin"
              />
            </div>

            <Button type="submit">Mesaji gonder</Button>
          </form>
        </Card>
      </div>
    </PageContainer>
  );
}
