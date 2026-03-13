import { For, createSignal, onCleanup, onMount } from "solid-js";
import styles from "./homeSections.module.css";

type Testimonial = {
  name: string;
  neighborhood: string;
  rating: number;
  comment: string;
  initials: string;
};

const testimonials: Testimonial[] = [
  {
    name: "Sude A.",
    neighborhood: "Kadikoy",
    rating: 4.9,
    comment: "Sabah saatlerinde sessiz mekanlari hizlica bulabiliyorum, odak surem ciddi artti.",
    initials: "SA",
  },
  {
    name: "Mert K.",
    neighborhood: "Besiktas",
    rating: 4.7,
    comment: "Priz ve Wi-Fi bilgisi net oldugu icin toplanti oncesi yer degistirme derdi kalmadi.",
    initials: "MK",
  },
  {
    name: "Buse C.",
    neighborhood: "Sisli",
    rating: 4.8,
    comment: "Masa rezervasyonu tarafi cok pratik, gittigimde dogrudan calismaya basliyorum.",
    initials: "BC",
  },
  {
    name: "Emir T.",
    neighborhood: "Uskudar",
    rating: 4.6,
    comment: "Yogun saatlerde bile alternatifleri gormek icin iyi bir referans kaynagi oldu.",
    initials: "ET",
  },
  {
    name: "Nisa Y.",
    neighborhood: "Kadikoy",
    rating: 5,
    comment: "Calisma dostu kafeleri semte gore filtreleyebilmek gercekten zaman kazandiriyor.",
    initials: "NY",
  },
];

export function Testimonials() {
  const [activeIndex, setActiveIndex] = createSignal(0);

  onMount(() => {
    const timer = window.setInterval(() => {
      setActiveIndex((current) => (current + 1) % testimonials.length);
    }, 4000);

    onCleanup(() => {
      window.clearInterval(timer);
    });
  });

  return (
    <section class={`${styles.testimonials} ${styles.reveal}`} data-reveal="true" aria-labelledby="testimonials-title">
      <h2 id="testimonials-title" class={styles.sectionHeader}>
        Kullanici Yorumlari
      </h2>
      <p class={styles.sectionSubtle}>Topluluktan gelen geribildirimler her hafta bu alanda guncellenir.</p>

      <div class={styles.testimonialStage} aria-live="polite">
        <For each={testimonials}>
          {(item, index) => (
            <article
              class={`${styles.testimonialCard} ${activeIndex() === index() ? styles.testimonialCardActive : ""}`}
              aria-hidden={activeIndex() !== index()}
            >
              <div class={styles.testimonialTop}>
                <span class={styles.initials} aria-hidden="true">
                  {item.initials}
                </span>
                <div>
                  <p class={styles.testimonialName}>
                    {item.name} • {item.rating.toFixed(1)}*
                  </p>
                  <p class={styles.testimonialNeighborhood}>{item.neighborhood}</p>
                </div>
              </div>
              <p class={styles.testimonialComment}>{item.comment}</p>
            </article>
          )}
        </For>
      </div>

      <div class={styles.dotNav} role="tablist" aria-label="Yorumlar arasinda gezinme">
        <For each={testimonials}>
          {(_, index) => (
            <button
              type="button"
              class={`${styles.dot} ${activeIndex() === index() ? styles.dotActive : ""}`}
              aria-label={`${index() + 1}. yorumu goster`}
              aria-pressed={activeIndex() === index()}
              onClick={() => setActiveIndex(index())}
            />
          )}
        </For>
      </div>
    </section>
  );
}
