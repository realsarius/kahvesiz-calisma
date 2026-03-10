import { A } from "@solidjs/router";
import { For, Show, createResource, createSignal } from "solid-js";
import { EmptyState } from "../components/states/EmptyState";
import { ErrorState } from "../components/states/ErrorState";
import { LoadingState } from "../components/states/LoadingState";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { PageContainer } from "../components/ui/PageContainer";
import { ApiRequestError } from "../lib/api";
import { getCafes } from "../lib/cafes";

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
  const [searchDraft, setSearchDraft] = createSignal("");
  const [search, setSearch] = createSignal("");
  const [cafes, { refetch }] = createResource(search, getCafes);

  const onSearchSubmit = (event: SubmitEvent) => {
    event.preventDefault();
    setSearch(searchDraft());
  };

  const clearSearch = () => {
    setSearchDraft("");
    setSearch("");
    void refetch();
  };

  return (
    <PageContainer title="Cafes" subtitle="Listeleme verisi /api/cafes endpointinden cekilir.">
      <Card>
        <form class="search-form" onSubmit={onSearchSubmit}>
          <Input
            id="search-cafe-list"
            label="Kafe ara"
            value={searchDraft()}
            onInput={(event) => setSearchDraft(event.currentTarget.value)}
            placeholder="Ornek: Besiktas"
            hint="Arama kelimesi backend search parametresine iletilir."
          />
          <div class="row-actions">
            <Button type="submit">Ara</Button>
            <Button type="button" variant="secondary" onClick={clearSearch}>
              Filtreyi temizle
            </Button>
          </div>
        </form>
      </Card>

      <Show when={!cafes.loading} fallback={<LoadingState title="Kafe listesi yukleniyor" />}>
        <Show
          when={!cafes.error}
          fallback={
            <ErrorState
              title="Kafe listesi alinamadi"
              description={readErrorMessage(cafes.error)}
              actionLabel="Tekrar dene"
              onAction={() => void refetch()}
            />
          }
        >
          <Show
            when={(cafes() ?? []).length > 0}
            fallback={
              <EmptyState
                title="Filtreye uygun kafe bulunamadi"
                description="Filtreyi temizleyip tekrar arayabilirsiniz."
                actionLabel="Filtreyi sifirla"
                onAction={clearSearch}
              />
            }
          >
            <Card>
              <ul class="cafe-list">
                <For each={cafes() ?? []}>
                  {(cafe) => (
                    <li class="cafe-list__item">
                      <div>
                        <A class="cafe-list__name-link" href={`/cafes/${cafe.id}`}>
                          {cafe.name}
                        </A>
                        <p class="cafe-list__meta">{cafe.location}</p>
                      </div>
                      <div class="chip-row">
                        <span class="ui-chip">wifi: {cafe.has_wifi ? "var" : "yok"}</span>
                        <span class="ui-chip">priz: {cafe.has_sockets ? "var" : "yok"}</span>
                        <span class="ui-chip">wc: {cafe.has_toilet ? "var" : "yok"}</span>
                        <span class="ui-chip">{cafe.coffee_price || "fiyat yok"}</span>
                      </div>
                    </li>
                  )}
                </For>
              </ul>
            </Card>
          </Show>
        </Show>
      </Show>
    </PageContainer>
  );
}
