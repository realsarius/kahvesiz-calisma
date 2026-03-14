import { A } from "@solidjs/router";
import { FiGrid, FiList } from "solid-icons/fi";
import { For, Show, createEffect, createMemo, createSignal, onCleanup } from "solid-js";
import { EmptyState } from "../components/states/EmptyState";
import { ErrorState } from "../components/states/ErrorState";
import { LoadingState } from "../components/states/LoadingState";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { PageContainer } from "../components/ui/PageContainer";
import { ApiRequestError } from "../lib/api";
import { type CafeListFilters, useInfiniteCafes } from "../lib/cafes";

type ViewMode = "table" | "grid";
type WifiFilterMode = "all" | "true" | "false";
type OutletFilterMode = "all" | "true" | "false";

const NOISE_OPTIONS = [
  { value: "silent", label: "Çok sessiz" },
  { value: "quiet", label: "Sessiz" },
  { value: "moderate", label: "Orta" },
  { value: "loud", label: "Gürültülü" },
] as const;

function formatNoiseLevel(noiseLevel: string | null | undefined) {
  const normalized = (noiseLevel || "").trim().toLowerCase();
  const option = NOISE_OPTIONS.find((item) => item.value === normalized);
  if (option) {
    return option.label;
  }
  return noiseLevel || "Bilinmiyor";
}

function readErrorMessage(error: unknown) {
  if (error instanceof ApiRequestError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Bilinmeyen hata";
}

export default function CafesPage() {
  const [neighborhoodDraft, setNeighborhoodDraft] = createSignal("");
  const [neighborhood, setNeighborhood] = createSignal("");
  const [wifiDraft, setWifiDraft] = createSignal<WifiFilterMode>("all");
  const [wifi, setWifi] = createSignal<WifiFilterMode>("all");
  const [outletDraft, setOutletDraft] = createSignal<OutletFilterMode>("all");
  const [outlet, setOutlet] = createSignal<OutletFilterMode>("all");
  const [noiseDraft, setNoiseDraft] = createSignal("");
  const [noise, setNoise] = createSignal("");
  const [viewMode, setViewMode] = createSignal<ViewMode>("table");
  let loadMoreSentinel: HTMLDivElement | undefined;

  const filters = createMemo<CafeListFilters>(() => ({
    neighborhood: neighborhood(),
    noiseLevel: noise(),
    wifi: wifi() === "all" ? null : wifi() === "true",
    hasOutlet: outlet() === "all" ? null : outlet() === "true",
    limit: 20,
  }));

  const cafes = useInfiniteCafes(filters);

  const onSearchSubmit = (event: SubmitEvent) => {
    event.preventDefault();
    setNeighborhood(neighborhoodDraft().trim().toLowerCase());
    setWifi(wifiDraft());
    setOutlet(outletDraft());
    setNoise(noiseDraft().trim().toLowerCase());
  };

  const clearSearch = () => {
    setNeighborhoodDraft("");
    setNeighborhood("");
    setWifiDraft("all");
    setWifi("all");
    setOutletDraft("all");
    setOutlet("all");
    setNoiseDraft("");
    setNoise("");
    cafes.retry();
  };

  createEffect(() => {
    const node = loadMoreSentinel;
    if (!node || !cafes.hasMore()) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (!entry?.isIntersecting) {
          return;
        }
        cafes.loadMore();
      },
      { rootMargin: "160px 0px 160px 0px" },
    );

    observer.observe(node);
    onCleanup(() => observer.disconnect());
  });

  return (
    <PageContainer title="Kafeler">
      <Card>
        <form class="search-form" onSubmit={onSearchSubmit}>
          <div class="grid-two-columns">
            <Input
              id="search-cafe-neighborhood"
              label="Semt"
              value={neighborhoodDraft()}
              onInput={(event) => setNeighborhoodDraft(event.currentTarget.value)}
              placeholder="Örnek: kadikoy"
              hint="Boş bırakırsanız tüm semtler listelenir."
            />

            <div class="ui-field">
              <label class="ui-field__label" for="filter-noise-level">
                Sessizlik seviyesi
              </label>
              <select
                id="filter-noise-level"
                class="ui-input ui-select"
                value={noiseDraft()}
                onChange={(event) => setNoiseDraft(event.currentTarget.value)}
              >
                <option value="">Hepsi</option>
                <For each={NOISE_OPTIONS}>
                  {(option) => <option value={option.value}>{option.label}</option>}
                </For>
              </select>
              <p class="ui-field__hint">Filtre backend’de `noise_level` parametresine gönderilir.</p>
            </div>
          </div>

          <div class="ui-field">
            <label class="ui-field__label" for="filter-wifi">
              Wi-Fi filtresi
            </label>
            <select
              id="filter-wifi"
              class="ui-input ui-select"
              value={wifiDraft()}
              onChange={(event) => setWifiDraft(event.currentTarget.value as WifiFilterMode)}
            >
              <option value="all">Hepsi</option>
              <option value="true">Sadece Wi-Fi olanlar</option>
              <option value="false">Sadece Wi-Fi olmayanlar</option>
            </select>
          </div>

          <div class="ui-field">
            <label class="ui-field__label" for="filter-outlet">
              Priz filtresi
            </label>
            <select
              id="filter-outlet"
              class="ui-input ui-select"
              value={outletDraft()}
              onChange={(event) => setOutletDraft(event.currentTarget.value as OutletFilterMode)}
            >
              <option value="all">Hepsi</option>
              <option value="true">Sadece priz olanlar</option>
              <option value="false">Priz olmayanlar</option>
            </select>
          </div>

          <div class="row-actions">
            <Button type="submit">Filtrele</Button>
            <Button type="button" variant="secondary" onClick={clearSearch}>
              Filtreleri temizle
            </Button>
          </div>
        </form>
      </Card>

      <Show when={!cafes.isLoadingInitial()} fallback={<LoadingState title="Kafe listesi yükleniyor" />}>
        <Show
          when={!cafes.error() || (cafes.items() ?? []).length > 0}
          fallback={
            <ErrorState
              title="Kafe listesi alınamadı"
              description={readErrorMessage(cafes.error())}
              actionLabel="Tekrar dene"
              onAction={cafes.retry}
            />
          }
        >
          <Show
            when={(cafes.items() ?? []).length > 0}
            fallback={
              <EmptyState
                title="Filtreye uygun kafe bulunamadı"
                description="Filtreyi temizleyip tekrar arayabilirsiniz."
                actionLabel="Filtreyi sıfırla"
                onAction={clearSearch}
              />
            }
          >
            <>
              <Card>
                <div class="cafes-toolbar">
                  <p class="cafes-toolbar__meta">
                    Görüntülenen <strong>{(cafes.items() ?? []).length}</strong> / Toplam{" "}
                    <strong>{cafes.totalCount()}</strong> kafe
                  </p>
                  <div class="view-switch" role="group" aria-label="Görünüm seçimi">
                    <button
                      type="button"
                      classList={{ "view-switch__button": true, active: viewMode() === "table" }}
                      onClick={() => setViewMode("table")}
                    >
                      <FiList class="view-switch__icon" aria-hidden="true" />
                      Tablo
                    </button>
                    <button
                      type="button"
                      classList={{ "view-switch__button": true, active: viewMode() === "grid" }}
                      onClick={() => setViewMode("grid")}
                    >
                      <FiGrid class="view-switch__icon" aria-hidden="true" />
                      Grid
                    </button>
                  </div>
                </div>
              </Card>

              <Show
                when={viewMode() === "table"}
                fallback={
                  <div class="cafe-grid">
                    <For each={cafes.items() ?? []}>
                      {(cafe) => (
                        <Card class="cafe-grid__card">
                          <div class="cafe-grid__header">
                            <A class="cafe-grid__title" href={`/cafes/${cafe.slug}`}>
                              {cafe.name}
                            </A>
                            <span class="ui-chip">⭐ {cafe.avg_rating.toFixed(1)}</span>
                          </div>
                          <p class="cafe-grid__location">{cafe.neighborhood || "Semt bilgisi yok"}</p>
                          <p class="cafe-grid__location">{cafe.address}</p>
                          <div class="chip-row">
                            <span
                              classList={{
                                "ui-chip": true,
                                "ui-chip--ok": cafe.wifi_available,
                                "ui-chip--no": !cafe.wifi_available,
                              }}
                            >
                              Wi-Fi: {cafe.wifi_available ? "Var" : "Yok"}
                            </span>
                            <span class="ui-chip">Gürültü: {formatNoiseLevel(cafe.noise_level)}</span>
                            <span class="ui-chip">Yorum: {cafe.review_count}</span>
                          </div>
                        </Card>
                      )}
                    </For>
                  </div>
                }
              >
                <Card>
                  <div class="cafe-table-wrap">
                    <table class="cafe-table">
                      <thead>
                        <tr>
                          <th>Kafe</th>
                          <th>Semt</th>
                          <th>Adres</th>
                          <th>Wi-Fi</th>
                          <th>Gürültü</th>
                          <th>Puan</th>
                          <th>Yorum</th>
                        </tr>
                      </thead>
                      <tbody>
                        <For each={cafes.items() ?? []}>
                          {(cafe) => (
                            <tr>
                              <td>
                                <A class="cafe-table__name" href={`/cafes/${cafe.slug}`}>
                                  {cafe.name}
                                </A>
                              </td>
                              <td>{cafe.neighborhood || "—"}</td>
                              <td>{cafe.address}</td>
                              <td>
                                <span
                                  classList={{
                                    "table-badge": true,
                                    "table-badge--ok": cafe.wifi_available,
                                    "table-badge--no": !cafe.wifi_available,
                                  }}
                                >
                                  {cafe.wifi_available ? "Var" : "Yok"}
                                </span>
                              </td>
                              <td>{formatNoiseLevel(cafe.noise_level)}</td>
                              <td>{cafe.avg_rating.toFixed(1)}</td>
                              <td>{cafe.review_count}</td>
                            </tr>
                          )}
                        </For>
                      </tbody>
                    </table>
                  </div>
                </Card>
              </Show>

              <Show when={cafes.error()}>
                <ErrorState
                  title="Sonraki sayfa yüklenemedi"
                  description={readErrorMessage(cafes.error())}
                  actionLabel="Tekrar dene"
                  onAction={cafes.retry}
                />
              </Show>

              <Show when={cafes.hasMore()}>
                <Card>
                  <div class="cafes-toolbar">
                    <p class="cafes-toolbar__meta">
                      {cafes.isLoadingMore() ? "Yeni sonuçlar yükleniyor..." : "Daha fazla sonuç yükleyebilirsiniz."}
                    </p>
                    <Button type="button" variant="secondary" onClick={cafes.loadMore} disabled={cafes.isLoadingMore()}>
                      {cafes.isLoadingMore() ? "Yükleniyor..." : "Daha fazla yükle"}
                    </Button>
                  </div>
                  <div ref={(el) => (loadMoreSentinel = el)} style={{ height: "1px", width: "100%" }} />
                </Card>
              </Show>
            </>
          </Show>
        </Show>
      </Show>
    </PageContainer>
  );
}
