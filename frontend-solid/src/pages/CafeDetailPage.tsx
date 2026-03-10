import { A, useParams } from "@solidjs/router";
import { Match, Show, Switch, createMemo, createResource } from "solid-js";
import { EmptyState } from "../components/states/EmptyState";
import { ErrorState } from "../components/states/ErrorState";
import { LoadingState } from "../components/states/LoadingState";
import { Card } from "../components/ui/Card";
import { PageContainer } from "../components/ui/PageContainer";
import { ApiRequestError } from "../lib/api";
import { getCafeById } from "../lib/cafes";

function readErrorMessage(error: unknown) {
  if (error instanceof ApiRequestError) {
    if (error.status === 404) {
      return "Kafe bulunamadi.";
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

  const cafeId = createMemo(() => {
    const parsed = Number.parseInt(params.id ?? "", 10);
    return Number.isNaN(parsed) ? null : parsed;
  });

  const [cafe, { refetch }] = createResource(cafeId, async (id) => {
    if (!id || id < 1) {
      throw new Error("Gecersiz kafe id");
    }
    return getCafeById(id);
  });

  return (
    <PageContainer
      title="Cafe detayi"
      subtitle="Detay verisi /api/cafes/:id endpointinden canli olarak cekilir."
      actions={
        <A class="ui-button ui-button--secondary ui-button--md" href="/cafes">
          Listeye don
        </A>
      }
    >
      <Show when={!cafe.loading} fallback={<LoadingState title="Kafe detayi yukleniyor" />}>
        <Show
          when={!cafe.error}
          fallback={
            <ErrorState
              title="Kafe detayi alinamadi"
              description={readErrorMessage(cafe.error)}
              actionLabel="Tekrar dene"
              onAction={() => void refetch()}
            />
          }
        >
          <Switch fallback={<EmptyState title="Kafe bulunamadi" />}>
            <Match when={Boolean(cafe())}>
              <Card>
                <div class="cafe-detail-grid">
                  <div class="cafe-detail-media">
                    <Show
                      when={cafe()?.img_url}
                      fallback={<div class="cafe-image-fallback">Gorsel yok</div>}
                    >
                      <img src={cafe()?.img_url || ""} alt={cafe()?.name || "Cafe"} class="cafe-image" />
                    </Show>
                  </div>

                  <div class="cafe-detail-main">
                    <p class="cafe-detail-name">{cafe()?.name}</p>
                    <p class="cafe-detail-location">{cafe()?.location}</p>

                    <div class="chip-row">
                      <span class="ui-chip">wifi: {cafe()?.has_wifi ? "var" : "yok"}</span>
                      <span class="ui-chip">priz: {cafe()?.has_sockets ? "var" : "yok"}</span>
                      <span class="ui-chip">wc: {cafe()?.has_toilet ? "var" : "yok"}</span>
                      <span class="ui-chip">cagri: {cafe()?.can_take_calls ? "uygun" : "uygun degil"}</span>
                      <span class="ui-chip">koltuk: {cafe()?.seats || "bilgi yok"}</span>
                      <span class="ui-chip">{cafe()?.coffee_price || "fiyat yok"}</span>
                    </div>

                    <Show when={cafe()?.details}>
                      <section class="details-block" innerHTML={cafe()?.details || ""} />
                    </Show>

                    <Show when={cafe()?.map_url}>
                      <A class="ui-link" href={cafe()?.map_url || "#"} target="_blank" rel="noreferrer">
                        Haritada ac
                      </A>
                    </Show>
                  </div>
                </div>
              </Card>
            </Match>
          </Switch>
        </Show>
      </Show>
    </PageContainer>
  );
}
