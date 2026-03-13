import { A } from "@solidjs/router";
import { Show } from "solid-js";
import { useAuth } from "../auth/AuthContext";
import { Alert } from "../components/ui/Alert";

export default function HomePage() {
  const auth = useAuth();

  return (
    <section class="home-hero-wrap">
      <Show when={auth.state.sessionExpired}>
        <Alert variant="warning" title="Oturum kapandı">
          Oturum süresi doldu. Yetkili işlemler için yeniden <A class="ui-link" href="/login">giriş</A> yapabilirsiniz.
        </Alert>
      </Show>
      <div class="home-hero-content">
        <h1 class="home-hero-title">Verimli Çalışma Alanları</h1>
        <p class="home-hero-description">
          Günümüzde iş yaparken verimliliği artırmak, doğru çalışma ortamını seçmekle başlar. Kafeler, hem rahat bir
          atmosfer sunar hem de sosyal etkileşim imkanı sağlar. Ancak herkes için uygun olmayabilirler.
        </p>
        <div class="home-hero-actions">
          <A href="/login" class="auth-button home-cta-primary">
            Şimdi Başlayın
          </A>
          <A href="/about" class="home-cta-secondary">
            Daha fazla bilgi <span aria-hidden="true">→</span>
          </A>
        </div>
      </div>
    </section>
  );
}
