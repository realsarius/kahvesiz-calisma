import { A, useParams } from "@solidjs/router";
import { FiMessageSquare, FiMonitor, FiStar, FiVolume2, FiWifi, FiZap } from "solid-icons/fi";
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

function formatNoiseLevel(level: string | null | undefined) {
  const key = (level || "").trim().toLowerCase();
  const labels: Record<string, string> = {
    silent: "sessiz",
    quiet: "sakin",
    moderate: "orta",
    loud: "yüksek",
  };
  return labels[key] || "bilinmiyor";
}

function formatSeatType(type: string) {
  const key = (type || "").trim().toLowerCase();
  const labels: Record<string, string> = {
    solo_desk: "Tek çalışma masası",
    shared_table: "Ortak masa",
    sofa: "Koltuk",
    bar: "Bar masası",
    outdoor: "Dış alan",
  };
  return labels[key] || type;
}

function formatCafeStatus(status: string | null | undefined) {
  const key = (status || "").trim().toLowerCase();
  const labels: Record<string, string> = {
    pending: "Beklemede",
    active: "Aktif",
    closed: "Kapalı",
    rejected: "Reddedildi",
  };
  return labels[key] || (status || "-");
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

  const formatDate = (value: string | null) => {
    if (!value) {
      return "";
    }
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return "";
    }
    return new Intl.DateTimeFormat("tr-TR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    }).format(parsed);
  };

  return (
    <PageContainer
      title="Kafe detayı"
      subtitle="Detay verisi canlı olarak veritabanından çekilir."
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
                      <span class="ui-chip">
                        <FiWifi class="ui-chip__icon" />
                        Wi-Fi: {cafe()?.amenities.wifi_available ? "Var" : "Yok"}
                      </span>
                      <span class="ui-chip">
                        <FiZap class="ui-chip__icon" />
                        Priz: {(cafe()?.amenities.outlet_count ?? 0) > 0 ? "Var" : "Yok"}
                      </span>
                      <span class="ui-chip">
                        <FiVolume2 class="ui-chip__icon" />
                        Gürültü: {formatNoiseLevel(cafe()?.amenities.noise_level)}
                      </span>
                      <span class="ui-chip">
                        <FiStar class="ui-chip__icon" />
                        Puan: {(cafe()?.avg_rating ?? 0).toFixed(1)}
                      </span>
                      <span class="ui-chip">
                        <FiMessageSquare class="ui-chip__icon" />
                        Yorum: {cafe()?.review_count ?? 0}
                      </span>
                      <span class="ui-chip">
                        <FiMonitor class="ui-chip__icon" />
                        Laptop: {cafe()?.amenities.allows_laptop ? "Uygun" : "Uygun değil"}
                      </span>
                    </div>

                    <Show when={cafe()?.description}>
                      <section class="details-block" innerHTML={cafe()?.description || ""} />
                    </Show>

                    <dl class="meta-list">
                      <div>
                        <dt>Durum</dt>
                        <dd>{formatCafeStatus(cafe()?.status)}</dd>
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
                            {formatSeatType(seat.seat_type)}: {seat.available_count}/{seat.total_count} boş
                          </li>
                        )}
                      </For>
                    </ul>
                  </Show>
                </Card>
              </div>

              <Card>
                <h3 class="ui-card__title">Son yorumlar</h3>
                <Show
                  when={(cafe()?.reviews ?? []).length > 0}
                  fallback={<p class="paragraph paragraph--compact">Bu kafe için henüz yorum görünmüyor.</p>}
                >
                  <ul class="review-list">
                    <For each={cafe()?.reviews ?? []}>
                      {(review) => (
                        <li class="review-list__item">
                          <div class="review-list__head">
                            <strong>{review.reviewer_name}</strong>
                            <span class="review-list__meta">Puan: {review.rating}/5</span>
                          </div>
                          <Show when={review.title}>
                            <p class="review-list__title">{review.title}</p>
                          </Show>
                          <Show when={review.body}>
                            <p class="paragraph paragraph--compact">{review.body}</p>
                          </Show>
                          <div class="review-list__meta">
                            <Show when={review.visited_at}>
                              <span>Ziyaret: {formatDate(review.visited_at)}</span>
                            </Show>
                            <span>Yorum: {formatDate(review.created_at)}</span>
                          </div>
                        </li>
                      )}
                    </For>
                  </ul>
                </Show>
              </Card>
            </Match>
          </Switch>
        </Show>
      </Show>
    </PageContainer>
  );
}
