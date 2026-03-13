import { For, createSignal } from "solid-js";
import styles from "./homeSections.module.css";

type FaqItem = {
  question: string;
  answer: string;
};

const faqItems: FaqItem[] = [
  {
    question: "Rezervasyon nasil calisiyor?",
    answer:
      "Kafe kartindan tarih ve saat secip onayladiginda rezervasyonun olusur. Mekana gittiginde adinla dogrulama yapilir.",
  },
  {
    question: "Puanlama sistemi neye gore belirleniyor?",
    answer:
      "Puanlar kullanici yorumlari, oturum sonrasi geri bildirimler ve mekan ici olanaklarin guncelligiyle birlikte hesaplanir.",
  },
  {
    question: "Yer bulma garantisi var mi?",
    answer:
      "Rezervasyon onayi alan kullanicilar icin ayrilan masalar icin garanti saglanir. Onaysiz ziyaretlerde doluluk durumuna gore yerlestirme yapilir.",
  },
  {
    question: "Kullanmak icin uyelik zorunlu mu?",
    answer:
      "Kafe listelerini gormek icin uye olman gerekmez. Rezervasyon, favori kaydetme ve yorum gonderme adimlarinda hesap gerekir.",
  },
  {
    question: "Kafemi platforma nasil eklerim?",
    answer:
      "Kafe Sahibi CTA alanindaki basvuru butonundan iletisim formunu doldurabilirsin. Ekip incelemesinden sonra profilin yayina alinir.",
  },
];

export function FAQ() {
  const [openIndex, setOpenIndex] = createSignal<number | null>(0);

  const toggle = (index: number) => {
    setOpenIndex((current) => (current === index ? null : index));
  };

  return (
    <section class={`${styles.faq} ${styles.reveal}`} data-reveal="true" aria-labelledby="faq-title">
      <h2 id="faq-title" class={styles.sectionHeader}>
        Sik Sorulan Sorular
      </h2>
      <div class={styles.faqList}>
        <For each={faqItems}>
          {(item, index) => {
            const answerId = `faq-answer-${index()}`;
            return (
              <article class={styles.faqItem}>
                <button
                  type="button"
                  class={styles.faqButton}
                  aria-label={`${item.question} sorusunu ac veya kapat`}
                  aria-expanded={openIndex() === index()}
                  aria-controls={answerId}
                  onClick={() => toggle(index())}
                >
                  {item.question}
                  <span class={styles.faqIcon} aria-hidden="true">
                    {openIndex() === index() ? "-" : "+"}
                  </span>
                </button>

                <div
                  id={answerId}
                  class={styles.faqAnswer}
                  style={{ "max-height": openIndex() === index() ? "180px" : "0px" }}
                  aria-hidden={openIndex() !== index()}
                >
                  <p class={styles.faqAnswerInner}>{item.answer}</p>
                </div>
              </article>
            );
          }}
        </For>
      </div>
    </section>
  );
}
