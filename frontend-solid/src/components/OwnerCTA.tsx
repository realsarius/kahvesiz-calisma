import { A } from "@solidjs/router";
import styles from "./homeSections.module.css";

export function OwnerCTA() {
  return (
    <section class={`${styles.ownerCta} ${styles.reveal}`} data-reveal="true" aria-labelledby="owner-cta-title">
      <div class={styles.ownerGrid}>
        <div>
          <h2 id="owner-cta-title" class={styles.sectionHeader}>
            Kafe Sahibi misin?
          </h2>
          <p class={styles.ownerLead}>
            Kafeni platforma ekleyerek yeni kullanicilara ulas, masa doluluk oranini artir ve calisma topluluguna
            dogrudan dahil ol.
          </p>
          <A href="/contact" class={styles.ownerButton} aria-label="Kafemi platforma ekle">
            Kafenimi Platforma Ekle
          </A>
        </div>

        <div class={styles.ownerMockup} aria-hidden="true">
          <div class={styles.mockupBar} />
          <div class={styles.mockupLine} />
          <div class={`${styles.mockupLine} ${styles.mockupLineShort}`} />
          <div class={styles.mockupCards}>
            <div class={styles.mockupCard} />
            <div class={styles.mockupCard} />
            <div class={styles.mockupCard} />
          </div>
        </div>
      </div>
    </section>
  );
}
