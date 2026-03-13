import { For, createSignal, onCleanup, onMount } from "solid-js";
import styles from "./homeSections.module.css";

type Stat = {
  caption: string;
  target: number;
  format: (value: number) => string;
};

const stats: Stat[] = [
  {
    caption: "Listelenen mekan",
    target: 127,
    format: (value) => `${Math.round(value).toLocaleString("tr-TR")} Kafe`,
  },
  {
    caption: "Tamamlanan oturum",
    target: 4200,
    format: (value) => `${Math.round(value).toLocaleString("tr-TR")}+ Seans`,
  },
  {
    caption: "Aktif semt",
    target: 38,
    format: (value) => `${Math.round(value).toLocaleString("tr-TR")} Semt`,
  },
  {
    caption: "Ortalama puan",
    target: 4.8,
    format: (value) => `${value.toFixed(1)}* Puan`,
  },
];

export function StatsBanner() {
  const [values, setValues] = createSignal(stats.map(() => 0));
  let bannerRef: HTMLElement | undefined;
  let timerId: number | undefined;
  let started = false;

  const startCountUp = () => {
    if (started) {
      return;
    }

    started = true;
    const startTime = performance.now();
    const duration = 1300;

    timerId = window.setInterval(() => {
      const elapsed = performance.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);

      setValues(stats.map((stat) => stat.target * progress));

      if (progress >= 1) {
        if (timerId) {
          window.clearInterval(timerId);
        }
        timerId = undefined;
      }
    }, 30);
  };

  onMount(() => {
    if (!bannerRef) {
      return;
    }

    if (!("IntersectionObserver" in window)) {
      startCountUp();
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) {
            return;
          }

          startCountUp();
          observer.disconnect();
        });
      },
      { threshold: 0.35 },
    );

    observer.observe(bannerRef);

    onCleanup(() => {
      observer.disconnect();
    });
  });

  onCleanup(() => {
    if (timerId) {
      window.clearInterval(timerId);
    }
  });

  return (
    <section
      class={`${styles.statsBanner} ${styles.reveal}`}
      data-reveal="true"
      aria-label="Platform istatistikleri"
      ref={bannerRef}
    >
      <div class={styles.statsGrid}>
        <For each={stats}>
          {(stat, index) => (
            <article class={styles.statItem} aria-label={stat.caption}>
              <p class={styles.statValue}>{stat.format(values()[index()] ?? 0)}</p>
              <p class={styles.statLabel}>{stat.caption}</p>
            </article>
          )}
        </For>
      </div>
    </section>
  );
}
