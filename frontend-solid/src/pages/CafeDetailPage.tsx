import { A, useParams } from "@solidjs/router";
import { For, Match, Show, Switch, createMemo, createResource } from "solid-js";
import { EmptyState } from "../components/states/EmptyState";
import { ErrorState } from "../components/states/ErrorState";
import { LoadingState } from "../components/states/LoadingState";
import { Card } from "../components/ui/Card";
import { PageContainer } from "../components/ui/PageContainer";
import { ApiRequestError } from "../lib/api";
import { getCafeBySlug } from "../lib/cafes";

function readErrorMessage(error: unknown) {
  if (error instanceof ApiRequestError) {
    if (error.status === 404) {
      return "Kafe bulunamadı.";
    }
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Bilinmeyen hata";
}

export default function CafeDetailPage() {
  const params = useParams();

  const cafeSlug = createMemo(() => (params.slug ?? "").trim());

  const [cafe, { refetch }] = createResource(cafeSlug, async (slug) => {
    if (!slug) {
      throw new Error("Geçersiz kafe slug");
    }
    return getCafeBySlug(slug);
  });

  const primaryImage = createMemo(() => {
    const images = cafe()?.images ?? [];
    return images.find((item) => item.is_primary) ?? images[0] ?? null;
  });

  const formatTime = (value: string | null) => {
    if (!value) {
      return "--:--";
    }
    return value.slice(0, 5);
  };

  const dayLabel = (day: number) => {
    const days = [
      "Pazartesi",
      "Salı",
      "Çarşamba",
      "Perşembe",
      "Cuma",
      "Cumartesi",
      "Pazar",
    ];
    return days[day] ?? `Gün ${day}`;
  };

  return (
    <PageContainer
      title="Kafe detayı"
      subtitle="Detay verisi /api/v1/cafes/:slug endpointinden canlı olarak çekilir."
      actions={
        <A class="ui-button ui-button--secondary ui-button--md" href="/cafes">
          Listeye dön
        </A>
      }
    >
      <Show when={!cafe.loading} fallback={<LoadingState title="Kafe detayı yükleniyor" />}>
        <Show
          when={!cafe.error}
          fallback={
            <ErrorState
              title="Kafe detayı alınamadı"
              description={readErrorMessage(cafe.error)}
              actionLabel="Tekrar dene"
              onAction={() => void refetch()}
            />
          }
        >
          <Switch fallback={<EmptyState title="Kafe bulunamadı" />}>
            <Match when={Boolean(cafe())}>
              <Card>
                <div class="cafe-detail-grid">
                  <div class="cafe-detail-media">
                    <Show
                      when={primaryImage()?.url}
                      fallback={<div class="cafe-image-fallback">Görsel yok</div>}
                    >
                      <img src={primaryImage()?.url || ""} alt={primaryImage()?.alt_text || cafe()?.name || "Kafe"} class="cafe-image" />
                    </Show>
                  </div>

                  <div class="cafe-detail-main">
                    <p class="cafe-detail-name">{cafe()?.name}</p>
                    <p class="cafe-detail-location">
                      {(cafe()?.neighborhood ? `${cafe()?.neighborhood} • ` : "") + (cafe()?.address ?? "")}
                    </p>

                    <div class="chip-row">
                      <span class="ui-chip">wifi: {cafe()?.amenities.wifi_available ? "var" : "yok"}</span>
                      <span class="ui-chip">priz: {(cafe()?.amenities.outlet_count ?? 0) > 0 ? "var" : "yok"}</span>
                      <span class="ui-chip">gürültü: {cafe()?.amenities.noise_level || "bilinmiyor"}</span>
                      <span class="ui-chip">puan: {(cafe()?.avg_rating ?? 0).toFixed(1)}</span>
                      <span class="ui-chip">yorum: {cafe()?.review_count ?? 0}</span>
                      <span class="ui-chip">laptop: {cafe()?.amenities.allows_laptop ? "uygun" : "uygun değil"}</span>
                    </div>

                    <Show when={cafe()?.description}>
                      <section class="details-block" innerHTML={cafe()?.description || ""} />
                    </Show>

                    <dl class="meta-list">
                      <div>
                        <dt>Durum</dt>
                        <dd>{cafe()?.status}</dd>
                      </div>
                      <div>
                        <dt>Doğrulanmış</dt>
                        <dd>{cafe()?.is_verified ? "Evet" : "Hayır"}</dd>
                      </div>
                      <div>
                        <dt>Kapasite</dt>
                        <dd>{cafe()?.total_capacity ?? "Belirtilmedi"}</dd>
                      </div>
                      <div>
                        <dt>Minimum harcama</dt>
                        <dd>{cafe()?.amenities.min_spend_try ? `${cafe()?.amenities.min_spend_try} TL` : "Belirtilmedi"}</dd>
                      </div>
                    </dl>

                    <Show when={cafe()?.google_maps_url}>
                      <A class="ui-link" href={cafe()?.google_maps_url || "#"} target="_blank" rel="noreferrer">
                        Haritada aç
                      </A>
                    </Show>
                  </div>
                </div>
              </Card>

              <div class="grid-two-columns">
                <Card>
                  <h3 class="ui-card__title">Çalışma saatleri</h3>
                  <Show when={(cafe()?.hours ?? []).length > 0} fallback={<p class="paragraph paragraph--compact">Saat bilgisi girilmemiş.</p>}>
                    <ul class="simple-list">
                      <For each={cafe()?.hours ?? []}>
                        {(hour) => (
                          <li>
                            {dayLabel(hour.day_of_week)}:{" "}
                            {hour.is_closed
                              ? "Kapalı"
                              : `${formatTime(hour.opens_at)} - ${formatTime(hour.closes_at)}`}
                          </li>
                        )}
                      </For>
                    </ul>
                  </Show>
                </Card>

                <Card>
                  <h3 class="ui-card__title">Oturma düzeni</h3>
                  <Show when={(cafe()?.seats ?? []).length > 0} fallback={<p class="paragraph paragraph--compact">Masa/koltuk detayı girilmemiş.</p>}>
                    <ul class="simple-list">
                      <For each={cafe()?.seats ?? []}>
                        {(seat) => (
                          <li>
                            {seat.seat_type}: {seat.available_count}/{seat.total_count} boş
                          </li>
                        )}
                      </For>
                    </ul>
                  </Show>
                </Card>
              </div>
            </Match>
          </Switch>
        </Show>
      </Show>
    </PageContainer>
  );
}
