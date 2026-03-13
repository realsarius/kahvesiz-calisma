import { A } from "@solidjs/router";
import { For, createSignal } from "solid-js";
import styles from "./homeSections.module.css";

type NoiseLevel = "quiet" | "moderate" | "loud";

type Cafe = {
  name: string;
  neighborhood: string;
  rating: number;
  wifi: boolean;
  outlets: boolean;
  noiseLevel: NoiseLevel;
  imageUrl: string;
};

const noiseLabel: Record<NoiseLevel, string> = {
  quiet: "Sessiz",
  moderate: "Orta",
  loud: "Hareketli",
};

const noiseIcon: Record<NoiseLevel, string> = {
  quiet: "S1",
  moderate: "S2",
  loud: "S3",
};

export function FeaturedCafes() {
  const [cafes] = createSignal<Cafe[]>([
    {
      name: "Mola Defteri",
      neighborhood: "Kadikoy",
      rating: 4.9,
      wifi: true,
      outlets: true,
      noiseLevel: "quiet",
      imageUrl:
        "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=960&q=80",
    },
    {
      name: "Pusula Coffee Lab",
      neighborhood: "Besiktas",
      rating: 4.7,
      wifi: true,
      outlets: true,
      noiseLevel: "moderate",
      imageUrl:
        "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=960&q=80",
    },
    {
      name: "Sessiz Cephe",
      neighborhood: "Sisli",
      rating: 4.8,
      wifi: true,
      outlets: false,
      noiseLevel: "quiet",
      imageUrl:
        "https://images.unsplash.com/photo-1521017432531-fbd92d768814?auto=format&fit=crop&w=960&q=80",
    },
    {
      name: "Atolye Masa",
      neighborhood: "Uskudar",
      rating: 4.6,
      wifi: true,
      outlets: true,
      noiseLevel: "moderate",
      imageUrl:
        "https://images.unsplash.com/photo-1513267048331-5611cad62e41?auto=format&fit=crop&w=960&q=80",
    },
    {
      name: "Dingin Fincan",
      neighborhood: "Kadikoy",
      rating: 4.5,
      wifi: true,
      outlets: false,
      noiseLevel: "quiet",
      imageUrl:
        "https://images.unsplash.com/photo-1521012012373-6a85bade18da?auto=format&fit=crop&w=960&q=80",
    },
    {
      name: "Northlight Brew",
      neighborhood: "Besiktas",
      rating: 4.7,
      wifi: true,
      outlets: true,
      noiseLevel: "loud",
      imageUrl:
        "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=960&q=80",
    },
  ]);

  return (
    <section
      class={`${styles.featuredCafes} ${styles.reveal}`}
      data-reveal="true"
      aria-labelledby="featured-cafes-title"
    >
      <header class={styles.featuredHeader}>
        <div>
          <h2 id="featured-cafes-title" class={styles.sectionHeader}>
            One Cikan Kafeler
          </h2>
          <p class={styles.sectionSubtle}>Bu hafta en cok tercih edilen calisma dostu mekanlar.</p>
        </div>
        <A href="/cafes" class={styles.linkArrow} aria-label="Tum kafeleri gor">
          Tum Kafeleri Gor -&gt;
        </A>
      </header>

      <div class={styles.cafeScroller} aria-label="One cikan kafeler kaydirma listesi">
        <For each={cafes()}>
          {(cafe) => (
            <article class={styles.cafeCard} aria-label={`${cafe.name} kafe karti`}>
              <img class={styles.cafeImage} src={cafe.imageUrl} alt={`${cafe.name} ic mekani`} loading="lazy" />
              <div class={styles.cafeBody}>
                <div class={styles.metaRow}>
                  <h3 class={styles.cafeName}>{cafe.name}</h3>
                  <span class={styles.rating}>{cafe.rating.toFixed(1)}*</span>
                </div>
                <div class={styles.metaRow}>
                  <span class={styles.badge}>{cafe.neighborhood}</span>
                </div>
                <div class={styles.featureList}>
                  <span class={styles.featureChip}>
                    <span aria-hidden="true">W</span>
                    {cafe.wifi ? "Wi-Fi var" : "Wi-Fi yok"}
                  </span>
                  <span class={styles.featureChip}>
                    <span aria-hidden="true">P</span>
                    {cafe.outlets ? "Priz var" : "Priz sinirli"}
                  </span>
                  <span class={styles.featureChip}>
                    <span aria-hidden="true">{noiseIcon[cafe.noiseLevel]}</span>
                    {noiseLabel[cafe.noiseLevel]}
                  </span>
                </div>
              </div>
            </article>
          )}
        </For>
      </div>
    </section>
  );
}
