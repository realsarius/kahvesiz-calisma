import { For, Show } from "solid-js";
import styles from "./homeSections.module.css";

type Step = {
  title: string;
  description: string;
};

const steps: Step[] = [
  {
    title: "Kafeni Sec",
    description: "Semtine ve calisma tarzina uygun kafeleri birkac saniyede kesfet.",
  },
  {
    title: "Masani Rezerve Et",
    description: "Saatini belirleyip musait masani yerinden kalkmadan ayirt.",
  },
  {
    title: "Calismaya Basla",
    description: "Geldiginde dogrudan yerine gec ve odaklanmaya hemen basla.",
  },
];

export function HowItWorks() {
  return (
    <section
      class={`${styles.howItWorks} ${styles.reveal}`}
      data-reveal="true"
      aria-labelledby="how-it-works-title"
    >
      <div class={styles.sectionContainer}>
        <h2 id="how-it-works-title" class={styles.sectionHeader}>
          Nasil Calisir?
        </h2>
        <p class={styles.sectionSubtle}>Uc kisa adimda kafeni bul, yerini ayarla ve uretkenlige gec.</p>
        <div class={styles.stepsTrack} role="list" aria-label="Calisma adimlari">
          <For each={steps}>
            {(step, index) => (
              <>
                <article class={styles.stepCard} role="listitem">
                  <span class={styles.stepNumber} aria-hidden="true">
                    {index() + 1}
                  </span>
                  <h3 class={styles.stepTitle}>{step.title}</h3>
                  <p class={styles.stepDescription}>{step.description}</p>
                </article>
                <Show when={index() < steps.length - 1}>
                  <span class={styles.stepArrow} aria-hidden="true">
                    -&gt;
                  </span>
                </Show>
              </>
            )}
          </For>
        </div>
      </div>
    </section>
  );
}
