import { Show, createSignal } from "solid-js";
import styles from "./homeSections.module.css";

export function Newsletter() {
  const [email, setEmail] = createSignal("");
  const [submitted, setSubmitted] = createSignal(false);

  const handleSubmit = (event: Event) => {
    event.preventDefault();

    if (!email().trim()) {
      return;
    }

    setSubmitted(true);
  };

  return (
    <section class={`${styles.newsletter} ${styles.reveal}`} data-reveal="true" aria-labelledby="newsletter-title">
      <div class={styles.newsletterInner}>
        <h2 id="newsletter-title" class={styles.sectionHeader}>
          Haftalik Kesfet Bulteni
        </h2>
        <p class={styles.sectionSubtle}>Yeni kafe onerileri ve semt trendlerini e-posta ile al.</p>

        <Show when={!submitted()} fallback={<p class={styles.newsletterMessage}>Abonelik tamamlandi. Hos geldin!</p>}>
          <form class={styles.newsletterForm} onSubmit={handleSubmit} aria-label="Bulten abonelik formu">
            <input
              type="email"
              class={styles.newsletterInput}
              value={email()}
              required
              placeholder="ornek@eposta.com"
              aria-label="E-posta adresi"
              onInput={(event) => setEmail(event.currentTarget.value)}
            />
            <button type="submit" class={styles.newsletterButton} aria-label="Bultene abone ol">
              Abone Ol
            </button>
          </form>
        </Show>
      </div>
    </section>
  );
}
