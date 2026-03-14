import { A } from "@solidjs/router";
import { For, Show, createResource } from "solid-js";
import { getCafesPageV1 } from "../lib/cafes";
import styles from "./homeSections.module.css";

const noiseLabel: Record<string, string> = {
  silent: "Çok Sessiz",
  quiet: "Sessiz",
  moderate: "Orta",
  loud: "Hareketli",
};

const noiseIcon: Record<string, string> = {
  silent: "S0",
  quiet: "S1",
  moderate: "S2",
  loud: "S3",
};

export function FeaturedCafes() {
  const [data] = createResource(() => getCafesPageV1({ limit: 6 }));

  return (
    <section
      class={`${styles.featuredCafes} ${styles.reveal}`}
      data-reveal="true"
      aria-labelledby="featured-cafes-title"
    >
      <header class={styles.featuredHeader}>
        <div>
          <h2 id="featured-cafes-title" class={styles.sectionHeader}>
            Öne Çıkan Kafeler
          </h2>
          <p class={styles.sectionSubtle}>Bu hafta en cok tercih edilen calisma dostu mekanlar.</p>
        </div>
        <A href="/cafes" class={styles.linkArrow} aria-label="Tum kafeleri gor">
          Tum Kafeleri Gor -&gt;
        </A>
      </header>

      <div class={styles.cafeScroller} aria-label="One cikan kafeler kaydirma listesi">
        <Show when={data.loading}>
            <div style={{ padding: "2rem", color: "var(--text-muted)" }}>Kafeler yükleniyor...</div>
        </Show>
        
        <Show when={data.error}>
            <div style={{ padding: "2rem", color: "var(--text-muted)" }}>Kafeler yüklenirken bir hata oluştu.</div>
        </Show>
        
        <Show when={data()}>
          {(payload) => (
            <For each={payload().items}>
              {(cafe, i) => {
                // Determine a nice placeholder image deterministic to the cafe index
                const imagePool = [
                  "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=640&q=80",
                  "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=640&q=80",
                  "https://images.unsplash.com/photo-1521017432531-fbd92d768814?auto=format&fit=crop&w=640&q=80",
                  "https://images.unsplash.com/photo-1513267048331-5611cad62e41?auto=format&fit=crop&w=640&q=80",
                  "https://images.unsplash.com/photo-1521012012373-6a85bade18da?auto=format&fit=crop&w=640&q=80",
                  "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=640&q=80"
                ];
                const coverImage = imagePool[i() % imagePool.length];
                const noise = cafe.noise_level || "moderate";

                return (
                  <article class={styles.cafeCard} aria-label={`${cafe.name} kafe karti`}>
                    <A href={`/cafes/${cafe.slug}`} style={{ "text-decoration": "none", color: "inherit", display: "flex", "flex-direction": "column", height: "100%" }}>
                      <img class={styles.cafeImage} src={coverImage} alt={`${cafe.name} ic mekani`} loading="lazy" />
                      <div class={styles.cafeBody} style={{ flex: 1 }}>
                        <div class={styles.metaRow}>
                          <h3 class={styles.cafeName} style={{ margin: 0 }}>{cafe.name}</h3>
                          <span class={styles.rating}>{cafe.avg_rating.toFixed(1)}*</span>
                        </div>
                        <div class={styles.metaRow} style={{ "margin-bottom": "auto" }}>
                          <span class={styles.badge}>{cafe.neighborhood || "Bilinmiyor"}</span>
                        </div>
                        <div class={styles.featureList} style={{ "margin-top": "1rem" }}>
                          <span class={styles.featureChip}>
                            <span aria-hidden="true">W</span>
                            {cafe.wifi_available ? "Wi-Fi var" : "Wi-Fi yok"}
                          </span>
                          <span class={styles.featureChip}>
                            <span aria-hidden="true">{noiseIcon[noise]}</span>
                            {noiseLabel[noise]}
                          </span>
                        </div>
                      </div>
                    </A>
                  </article>
                );
              }}
            </For>
          )}
        </Show>
      </div>
    </section>
  );
}
