import { A, useParams } from "@solidjs/router";
import { FiMonitor, FiMessageSquare, FiStar, FiVolume2, FiWifi, FiZap } from "solid-icons/fi";
import { For, Match, Show, Switch, createEffect, createMemo, createResource, createSignal } from "solid-js";
import { useAuth } from "../auth/AuthContext";
import { EmptyState } from "../components/states/EmptyState";
import { ErrorState } from "../components/states/ErrorState";
import { LoadingState } from "../components/states/LoadingState";
import { Card } from "../components/ui/Card";
import { PageContainer } from "../components/ui/PageContainer";
import { ApiRequestError } from "../lib/api";
import { getCafeBySlug } from "../lib/cafes";
import {
  clearReviewVote,
  createCafeReview,
  deleteCafeReview,
  getCafeReviews,
  setReviewVote,
  type ReviewItemV1,
  type ReviewVote,
} from "../lib/reviews";

type CafeDetailTab = "details" | "reviews";

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

function mergeReviewItems(previous: ReviewItemV1[], incoming: ReviewItemV1[]) {
  const merged = [...previous];
  const existingIds = new Set(previous.map((item) => item.id));
  for (const item of incoming) {
    if (!existingIds.has(item.id)) {
      merged.push(item);
      existingIds.add(item.id);
    }
  }
  return merged;
}

function formatStarRating(rating: number) {
  const safe = Math.max(1, Math.min(5, Math.round(rating)));
  return `${"★".repeat(safe)}${"☆".repeat(5 - safe)}`;
}

export default function CafeDetailPage() {
  const params = useParams();
  const auth = useAuth();

  const [activeTab, setActiveTab] = createSignal<CafeDetailTab>("details");

  const [reviewRating, setReviewRating] = createSignal(5);
  const [reviewTitle, setReviewTitle] = createSignal("");
  const [reviewBody, setReviewBody] = createSignal("");
  const [reviewSubmitLoading, setReviewSubmitLoading] = createSignal(false);
  const [reviewFormError, setReviewFormError] = createSignal<string | null>(null);
  const [reviewActionError, setReviewActionError] = createSignal<string | null>(null);
  const [reviewDeleteLoadingId, setReviewDeleteLoadingId] = createSignal<string | null>(null);
  const [reviewVoteLoadingId, setReviewVoteLoadingId] = createSignal<string | null>(null);

  const [reviewCursor, setReviewCursor] = createSignal<string | null>(null);
  const [reviewItems, setReviewItems] = createSignal<ReviewItemV1[]>([]);
  const [reviewNextCursor, setReviewNextCursor] = createSignal<string | null>(null);
  const [reviewTotalCount, setReviewTotalCount] = createSignal(0);
  const [reviewLoadedOnce, setReviewLoadedOnce] = createSignal(false);
  const [reviewReloadToken, setReviewReloadToken] = createSignal(0);

  const cafeSlug = createMemo(() => (params.slug ?? "").trim());
  const loginHref = createMemo(() => `/login?redirect=${encodeURIComponent(`/cafes/${cafeSlug()}`)}`);

  const [cafe, { refetch }] = createResource(cafeSlug, async (slug) => {
    if (!slug) {
      throw new Error("Geçersiz kafe slug");
    }
    return getCafeBySlug(slug);
  });

  const [reviewsPage, { refetch: refetchReviewsPage }] = createResource(
    createMemo(() => ({
      cafeId: cafe()?.id ?? "",
      cursor: reviewCursor(),
      reloadToken: reviewReloadToken(),
    })),
    async (source) => {
      if (!source.cafeId) {
        return null;
      }
      return getCafeReviews(source.cafeId, { cursor: source.cursor, limit: 10 });
    },
  );

  createEffect(() => {
    cafe()?.id;
    setReviewCursor(null);
    setReviewItems([]);
    setReviewNextCursor(null);
    setReviewTotalCount(0);
    setReviewLoadedOnce(false);
    setReviewFormError(null);
    setReviewActionError(null);
  });

  createEffect(() => {
    const payload = reviewsPage();
    if (!payload) {
      return;
    }

    if (reviewCursor() === null) {
      setReviewItems(payload.items);
    } else {
      setReviewItems((previous) => mergeReviewItems(previous, payload.items));
    }

    setReviewNextCursor(payload.next_cursor ?? null);
    setReviewTotalCount(payload.total_count ?? 0);
    setReviewLoadedOnce(true);
  });

  const currentUserId = createMemo(() => {
    const rawId = auth.state.user?.id;
    if (rawId === null || rawId === undefined) {
      return null;
    }
    return String(rawId);
  });

  const primaryImage = createMemo(() => {
    const images = cafe()?.images ?? [];
    return images.find((item) => item.is_primary) ?? images[0] ?? null;
  });

  const reviewsHasMore = createMemo(() => Boolean(reviewNextCursor()));
  const reviewsInitialLoading = createMemo(() => reviewsPage.loading && !reviewLoadedOnce());
  const reviewsLoadingMore = createMemo(() => reviewsPage.loading && reviewLoadedOnce() && reviewCursor() !== null);

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

  const refreshReviews = () => {
    setReviewCursor(null);
    setReviewItems([]);
    setReviewNextCursor(null);
    setReviewTotalCount(0);
    setReviewLoadedOnce(false);
    setReviewReloadToken((value) => value + 1);
  };

  const loadMoreReviews = () => {
    if (reviewsPage.loading) {
      return;
    }

    const next = reviewNextCursor();
    if (!next) {
      return;
    }

    setReviewCursor(next);
  };

  const canDeleteReview = (item: ReviewItemV1) => {
    const userId = currentUserId();
    if (!userId) {
      return false;
    }

    const role = (auth.state.user?.role || "").trim().toLowerCase();
    if (auth.state.user?.isAdmin || role === "moderator" || role === "mod") {
      return true;
    }

    return item.user_id === userId;
  };

  const submitReview = async (event: SubmitEvent) => {
    event.preventDefault();

    const cafeId = cafe()?.id;
    if (!cafeId) {
      setReviewFormError("Yorum gönderilemedi. Kafe bilgisi eksik.");
      return;
    }

    if (!auth.state.isAuthenticated) {
      setReviewFormError("Yorum yazmak için giriş yapmanız gerekiyor.");
      return;
    }

    const cleanTitle = reviewTitle().trim();
    const cleanBody = reviewBody().trim();

    if (!cleanBody && !cleanTitle) {
      setReviewFormError("Başlık veya yorum metni girmeniz gerekiyor.");
      return;
    }

    setReviewSubmitLoading(true);
    setReviewFormError(null);

    try {
      await createCafeReview(cafeId, {
        rating: reviewRating(),
        title: cleanTitle || null,
        body: cleanBody || null,
      });
      setReviewTitle("");
      setReviewBody("");
      setReviewRating(5);
      refreshReviews();
      void refetch();
    } catch (error) {
      setReviewFormError(readErrorMessage(error));
    } finally {
      setReviewSubmitLoading(false);
    }
  };

  const removeReview = async (reviewId: string) => {
    const confirmed = window.confirm("Bu yorumu silmek istediğinize emin misiniz?");
    if (!confirmed) {
      return;
    }

    setReviewDeleteLoadingId(reviewId);
    setReviewActionError(null);

    try {
      await deleteCafeReview(reviewId);
      refreshReviews();
      void refetch();
    } catch (error) {
      setReviewActionError(readErrorMessage(error));
    } finally {
      setReviewDeleteLoadingId(null);
    }
  };

  const toggleVote = async (item: ReviewItemV1, targetVote: ReviewVote) => {
    setReviewVoteLoadingId(item.id);
    setReviewActionError(null);

    try {
      if (item.my_vote === targetVote) {
        await clearReviewVote(item.id);
      } else {
        await setReviewVote(item.id, targetVote);
      }
      refreshReviews();
    } catch (error) {
      setReviewActionError(readErrorMessage(error));
    } finally {
      setReviewVoteLoadingId(null);
    }
  };

  return (
    <PageContainer
      title={cafe()?.name || "Kafe"}
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
                      <img
                        src={primaryImage()?.url || ""}
                        alt={primaryImage()?.alt_text || cafe()?.name || "Kafe"}
                        class="cafe-image"
                      />
                    </Show>
                  </div>

                  <div class="cafe-detail-main">
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
                      <section class="details-block">
                        <For each={(cafe()?.description || "").split("\n")}>
                          {(paragraph) => (
                            <Show when={paragraph.trim()}>
                              <p>{paragraph}</p>
                            </Show>
                          )}
                        </For>
                      </section>
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
                        <dd>
                          {cafe()?.amenities.min_spend_try
                            ? `${cafe()?.amenities.min_spend_try} TL`
                            : "Belirtilmedi"}
                        </dd>
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

              <Card>
                <div class="detail-tabs" role="tablist" aria-label="Kafe detay sekmeleri">
                  <button
                    type="button"
                    role="tab"
                    classList={{ "detail-tabs__button": true, active: activeTab() === "details" }}
                    aria-selected={activeTab() === "details"}
                    onClick={() => setActiveTab("details")}
                  >
                    Kafe detayları
                  </button>
                  <button
                    type="button"
                    role="tab"
                    classList={{ "detail-tabs__button": true, active: activeTab() === "reviews" }}
                    aria-selected={activeTab() === "reviews"}
                    onClick={() => setActiveTab("reviews")}
                  >
                    Yorumlar
                  </button>
                </div>
              </Card>

              <Show when={activeTab() === "details"}>
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
              </Show>

              <Show when={activeTab() === "reviews"}>
                <Card>
                  <h3 class="ui-card__title">Yorum yaz</h3>
                  <Show
                    when={auth.state.isAuthenticated}
                    fallback={
                      <p class="paragraph paragraph--compact">
                        Yorum eklemek için <A class="ui-link" href={loginHref()}>giriş yapmanız</A> gerekiyor.
                      </p>
                    }
                  >
                    <Show when={reviewFormError()}>
                      {(message) => <p class="ui-field__error">{message()}</p>}
                    </Show>

                    <form class="review-form" onSubmit={submitReview}>
                      <div class="ui-field">
                        <label class="ui-field__label" for="review-rating">
                          Puan
                        </label>
                        <div id="review-rating" class="review-stars" role="radiogroup" aria-label="Puan seçimi">
                          <For each={[1, 2, 3, 4, 5]}>
                            {(score) => (
                              <button
                                type="button"
                                classList={{
                                  "review-stars__button": true,
                                  active: reviewRating() === score,
                                }}
                                onClick={() => setReviewRating(score)}
                              >
                                <span aria-hidden="true">{score <= reviewRating() ? "★" : "☆"}</span>
                                <span>{score}</span>
                              </button>
                            )}
                          </For>
                        </div>
                      </div>

                      <div class="ui-field">
                        <label class="ui-field__label" for="review-title">
                          Başlık
                        </label>
                        <input
                          id="review-title"
                          class="ui-input"
                          value={reviewTitle()}
                          maxlength={200}
                          placeholder="Kısa bir başlık"
                          onInput={(event) => setReviewTitle(event.currentTarget.value)}
                        />
                      </div>

                      <div class="ui-field">
                        <label class="ui-field__label" for="review-body">
                          Yorum
                        </label>
                        <textarea
                          id="review-body"
                          class="ui-input ui-textarea"
                          placeholder="Deneyiminizi paylaşın"
                          value={reviewBody()}
                          onInput={(event) => setReviewBody(event.currentTarget.value)}
                        />
                      </div>

                      <div class="row-actions">
                        <button
                          type="submit"
                          class="ui-button ui-button--primary ui-button--md"
                          disabled={reviewSubmitLoading()}
                        >
                          {reviewSubmitLoading() ? "Gönderiliyor..." : "Yorumu gönder"}
                        </button>
                      </div>
                    </form>
                  </Show>
                </Card>

                <Show when={!reviewsInitialLoading()} fallback={<LoadingState title="Yorumlar yükleniyor" />}>
                  <Show
                    when={!reviewsPage.error || (reviewItems() ?? []).length > 0}
                    fallback={
                      <ErrorState
                        title="Yorumlar alınamadı"
                        description={readErrorMessage(reviewsPage.error)}
                        actionLabel="Tekrar dene"
                        onAction={() => void refetchReviewsPage()}
                      />
                    }
                  >
                    <Card>
                      <h3 class="ui-card__title">Yorumlar ({reviewTotalCount()})</h3>

                      <Show when={reviewActionError()}>
                        {(message) => <p class="ui-field__error">{message()}</p>}
                      </Show>

                      <Show
                        when={(reviewItems() ?? []).length > 0}
                        fallback={<p class="paragraph paragraph--compact">Bu kafe için henüz yorum görünmüyor.</p>}
                      >
                        <ul class="review-list">
                          <For each={reviewItems() ?? []}>
                            {(review) => (
                              <li class="review-list__item">
                                <div class="review-list__head">
                                  <strong>{review.reviewer_name}</strong>
                                  <span class="review-list__meta">{formatStarRating(review.rating)}</span>
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

                                <div class="review-list__actions">
                                  <div class="review-vote-group" role="group" aria-label="Yorum oylama">
                                    <button
                                      type="button"
                                      classList={{
                                        "review-vote-button": true,
                                        active: review.my_vote === "helpful",
                                      }}
                                      disabled={reviewVoteLoadingId() === review.id}
                                      onClick={() => void toggleVote(review, "helpful")}
                                    >
                                      Yararlı ({review.helpful_count})
                                    </button>
                                    <button
                                      type="button"
                                      classList={{
                                        "review-vote-button": true,
                                        active: review.my_vote === "unhelpful",
                                      }}
                                      disabled={reviewVoteLoadingId() === review.id}
                                      onClick={() => void toggleVote(review, "unhelpful")}
                                    >
                                      Yararsız ({review.unhelpful_count})
                                    </button>
                                  </div>

                                  <Show when={canDeleteReview(review)}>
                                    <button
                                      type="button"
                                      class="ui-button ui-button--danger ui-button--sm"
                                      disabled={reviewDeleteLoadingId() === review.id}
                                      onClick={() => void removeReview(review.id)}
                                    >
                                      {reviewDeleteLoadingId() === review.id ? "Siliniyor..." : "Yorumu sil"}
                                    </button>
                                  </Show>
                                </div>
                              </li>
                            )}
                          </For>
                        </ul>
                      </Show>

                      <Show when={Boolean(reviewsPage.error) && (reviewItems() ?? []).length > 0}>
                        <p class="ui-field__error">{readErrorMessage(reviewsPage.error)}</p>
                      </Show>

                      <Show when={reviewsHasMore()}>
                        <div class="row-actions">
                          <button
                            type="button"
                            class="ui-button ui-button--secondary ui-button--md"
                            disabled={reviewsLoadingMore()}
                            onClick={loadMoreReviews}
                          >
                            {reviewsLoadingMore() ? "Yükleniyor..." : "Daha fazla yorum yükle"}
                          </button>
                        </div>
                      </Show>
                    </Card>
                  </Show>
                </Show>
              </Show>
            </Match>
          </Switch>
        </Show>
      </Show>
    </PageContainer>
  );
}
