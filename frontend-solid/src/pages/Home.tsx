import { A } from "@solidjs/router";
import { Show, onCleanup, onMount } from "solid-js";
import { useAuth } from "../auth/AuthContext";
import { FAQ } from "../components/FAQ";
import { FeaturedCafes } from "../components/FeaturedCafes";
import { HowItWorks } from "../components/HowItWorks";
import { Newsletter } from "../components/Newsletter";
import { OwnerCTA } from "../components/OwnerCTA";
import { SearchPreview } from "../components/SearchPreview";
import { StatsBanner } from "../components/StatsBanner";
import { Testimonials } from "../components/Testimonials";
import styles from "../components/homeSections.module.css";
import { Alert } from "../components/ui/Alert";

export default function Home() {
  const auth = useAuth();

  onMount(() => {
    const revealSections = Array.from(document.querySelectorAll<HTMLElement>("[data-reveal='true']"));

    if (!revealSections.length) {
      return;
    }

    const makeVisible = (section: HTMLElement) => {
      section.setAttribute("data-visible", "true");
    };

    if (!("IntersectionObserver" in window)) {
      revealSections.forEach(makeVisible);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) {
            return;
          }

          const section = entry.target as HTMLElement;
          makeVisible(section);
          observer.unobserve(section);
        });
      },
      { threshold: 0.2, rootMargin: "0px 0px -8% 0px" },
    );

    revealSections.forEach((section) => {
      section.setAttribute("data-visible", "false");
      observer.observe(section);
    });

    onCleanup(() => {
      observer.disconnect();
    });
  });

  return (
    <main class={styles.homePage}>
      <Show when={auth.state.sessionExpired}>
        <div class={styles.alertWrap}>
          <Alert variant="warning" title="Oturum kapandi">
            Oturum suresi doldu. Yetkili islemler icin yeniden{" "}
            <A class="ui-link" href="/login">
              giris
            </A>{" "}
            yapabilirsiniz.
          </Alert>
        </div>
      </Show>

      <section class="home-hero-wrap">
        <div class="home-hero-content">
          <h1 class="home-hero-title">Kahvesiz Calisma ile Verimli Alanlar</h1>
          <p class="home-hero-description">
            Dogru kahve ve dogru masa bir araya geldiginde gunun ritmi degisir. Semtine uygun kafe sec, yerini ayarla
            ve calismaya odaklan.
          </p>
          <div class="home-hero-actions">
            <A href="/cafes" class="auth-button home-cta-primary" aria-label="Kafeleri kesfet">
              Kafeleri Kesfet
            </A>
            <A href="/about" class="home-cta-secondary" aria-label="Platform hakkinda daha fazla bilgi al">
              Daha fazla bilgi <span aria-hidden="true">-&gt;</span>
            </A>
          </div>
        </div>
      </section>

      <HowItWorks />
      <FeaturedCafes />
      <StatsBanner />
      <SearchPreview />
      <Testimonials />
      <OwnerCTA />
      <FAQ />
      <Newsletter />
    </main>
  );
}
