import { A } from "@solidjs/router";
import { For, Show, createMemo, createSignal } from "solid-js";
import styles from "./homeSections.module.css";

type SearchCafe = {
  name: string;
  neighborhood: "Kadikoy" | "Besiktas" | "Sisli" | "Uskudar";
  wifi: boolean;
  quiet: boolean;
  rating: number;
};

const districts: SearchCafe["neighborhood"][] = ["Kadikoy", "Besiktas", "Sisli", "Uskudar"];

const cafes: SearchCafe[] = [
  { name: "Mola Defteri", neighborhood: "Kadikoy", wifi: true, quiet: true, rating: 4.9 },
  { name: "Kuzey Masasi", neighborhood: "Besiktas", wifi: true, quiet: false, rating: 4.6 },
  { name: "Dingin Fincan", neighborhood: "Kadikoy", wifi: true, quiet: true, rating: 4.5 },
  { name: "Atolye Masa", neighborhood: "Uskudar", wifi: true, quiet: false, rating: 4.4 },
  { name: "Sessiz Cephe", neighborhood: "Sisli", wifi: true, quiet: true, rating: 4.8 },
  { name: "Merkez Demleme", neighborhood: "Sisli", wifi: false, quiet: true, rating: 4.3 },
  { name: "Rota Kahve", neighborhood: "Besiktas", wifi: true, quiet: true, rating: 4.7 },
  { name: "Ruzgar Study", neighborhood: "Uskudar", wifi: true, quiet: true, rating: 4.6 },
];

export function SearchPreview() {
  const [selectedDistrict, setSelectedDistrict] = createSignal<string>("Tum Semtler");
  const [wifiOnly, setWifiOnly] = createSignal(false);
  const [quietOnly, setQuietOnly] = createSignal(false);

  const filteredResults = createMemo(() => {
    return cafes
      .filter((cafe) => (selectedDistrict() === "Tum Semtler" ? true : cafe.neighborhood === selectedDistrict()))
      .filter((cafe) => (wifiOnly() ? cafe.wifi : true))
      .filter((cafe) => (quietOnly() ? cafe.quiet : true))
      .slice(0, 3);
  });

  return (
    <section class={`${styles.searchPreview} ${styles.reveal}`} data-reveal="true" aria-labelledby="search-preview-title">
      <h2 id="search-preview-title" class={styles.sectionHeader}>
        Arama Onizlemesi
      </h2>
      <p class={styles.sectionSubtle}>Semt ve filtreleri degistir, onerilen sonuclar aninda guncellensin.</p>

      <div class={styles.searchControls}>
        <select
          class={styles.selectControl}
          aria-label="Semt secimi"
          value={selectedDistrict()}
          onInput={(event) => setSelectedDistrict(event.currentTarget.value)}
        >
          <option value="Tum Semtler">Tum Semtler</option>
          <For each={districts}>{(district) => <option value={district}>{district}</option>}</For>
        </select>

        <label class={styles.toggleControl}>
          <input
            type="checkbox"
            checked={wifiOnly()}
            onChange={(event) => setWifiOnly(event.currentTarget.checked)}
            aria-label="Sadece Wi-Fi olanlar"
          />
          Wi-Fi
        </label>

        <label class={styles.toggleControl}>
          <input
            type="checkbox"
            checked={quietOnly()}
            onChange={(event) => setQuietOnly(event.currentTarget.checked)}
            aria-label="Sadece sessiz ortam"
          />
          Sessizlik
        </label>
      </div>

      <Show when={filteredResults().length > 0} fallback={<p class={styles.searchEmpty}>Bu filtreyle sonuc bulunamadi.</p>}>
        <div class={styles.searchResults}>
          <For each={filteredResults()}>
            {(result) => (
              <article class={styles.searchCard} aria-label={`${result.name} arama sonucu`}>
                <h3 class={styles.searchCardTitle}>{result.name}</h3>
                <p class={styles.searchMeta}>
                  {result.neighborhood} • {result.rating.toFixed(1)}* • {result.wifi ? "Wi-Fi var" : "Wi-Fi yok"} •{" "}
                  {result.quiet ? "Sessiz" : "Orta ses"}
                </p>
              </article>
            )}
          </For>
        </div>
      </Show>

      <div class={styles.searchCta}>
        <A href="/cafes" class={styles.searchButton} aria-label="Tam arama sayfasina git">
          Tam Arama Sayfasina Git
        </A>
      </div>
    </section>
  );
}
