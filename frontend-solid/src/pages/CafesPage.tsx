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

type ViewMode = "table" | "grid";

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
  const [viewMode, setViewMode] = createSignal<ViewMode>("table");
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
    <PageContainer title="Kafeler" subtitle="Listeleme verisi /api/cafes endpointinden çekilir.">
      <Card>
        <form class="search-form" onSubmit={onSearchSubmit}>
          <Input
            id="search-cafe-list"
            label="Kafe ara"
            value={searchDraft()}
            onInput={(event) => setSearchDraft(event.currentTarget.value)}
            placeholder="Örnek: Beşiktaş"
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
                    Toplam <strong>{(cafes() ?? []).length}</strong> kafe
                  </p>
                  <div class="view-switch" role="group" aria-label="Gorunum secimi">
                    <button
                      type="button"
                      classList={{ "view-switch__button": true, active: viewMode() === "table" }}
                      onClick={() => setViewMode("table")}
                    >
                      Tablo
                    </button>
                    <button
                      type="button"
                      classList={{ "view-switch__button": true, active: viewMode() === "grid" }}
                      onClick={() => setViewMode("grid")}
                    >
                      Grid
                    </button>
                  </div>
                </div>
              </Card>

              <Show
                when={viewMode() === "table"}
                fallback={
                  <div class="cafe-grid">
                    <For each={cafes() ?? []}>
                      {(cafe) => (
                        <Card class="cafe-grid__card">
                          <div class="cafe-grid__header">
                            <A class="cafe-grid__title" href={`/cafes/${cafe.id}`}>
                              {cafe.name}
                            </A>
                            <span class="ui-chip">{cafe.coffee_price || "fiyat yok"}</span>
                          </div>
                          <p class="cafe-grid__location">{cafe.location}</p>
                          <div class="chip-row">
                            <span classList={{ "ui-chip": true, "ui-chip--ok": cafe.has_wifi, "ui-chip--no": !cafe.has_wifi }}>
                              Wi-Fi: {cafe.has_wifi ? "Var" : "Yok"}
                            </span>
                            <span
                              classList={{ "ui-chip": true, "ui-chip--ok": cafe.has_sockets, "ui-chip--no": !cafe.has_sockets }}
                            >
                              Priz: {cafe.has_sockets ? "Var" : "Yok"}
                            </span>
                            <span
                              classList={{ "ui-chip": true, "ui-chip--ok": cafe.has_toilet, "ui-chip--no": !cafe.has_toilet }}
                            >
                              WC: {cafe.has_toilet ? "Var" : "Yok"}
                            </span>
                            <span
                              classList={{
                                "ui-chip": true,
                                "ui-chip--ok": cafe.can_take_calls,
                                "ui-chip--no": !cafe.can_take_calls,
                              }}
                            >
                              Çağrı: {cafe.can_take_calls ? "Uygun" : "Uygun değil"}
                            </span>
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
                          <th>Konum</th>
                          <th>Wi-Fi</th>
                          <th>Priz</th>
                          <th>WC</th>
                          <th>Çağrı</th>
                          <th>Kahve</th>
                        </tr>
                      </thead>
                      <tbody>
                        <For each={cafes() ?? []}>
                          {(cafe) => (
                            <tr>
                              <td>
                                <A class="cafe-table__name" href={`/cafes/${cafe.id}`}>
                                  {cafe.name}
                                </A>
                              </td>
                              <td>{cafe.location}</td>
                              <td>
                                <span classList={{ "table-badge": true, "table-badge--ok": cafe.has_wifi, "table-badge--no": !cafe.has_wifi }}>
                                  {cafe.has_wifi ? "Var" : "Yok"}
                                </span>
                              </td>
                              <td>
                                <span
                                  classList={{
                                    "table-badge": true,
                                    "table-badge--ok": cafe.has_sockets,
                                    "table-badge--no": !cafe.has_sockets,
                                  }}
                                >
                                  {cafe.has_sockets ? "Var" : "Yok"}
                                </span>
                              </td>
                              <td>
                                <span
                                  classList={{
                                    "table-badge": true,
                                    "table-badge--ok": cafe.has_toilet,
                                    "table-badge--no": !cafe.has_toilet,
                                  }}
                                >
                                  {cafe.has_toilet ? "Var" : "Yok"}
                                </span>
                              </td>
                              <td>
                                <span
                                  classList={{
                                    "table-badge": true,
                                    "table-badge--ok": cafe.can_take_calls,
                                    "table-badge--no": !cafe.can_take_calls,
                                  }}
                                >
                                  {cafe.can_take_calls ? "Uygun" : "Değil"}
                                </span>
                              </td>
                              <td>{cafe.coffee_price || "fiyat yok"}</td>
                            </tr>
                          )}
                        </For>
                      </tbody>
                    </table>
                  </div>
                </Card>
              </Show>
            </>
          </Show>
        </Show>
      </Show>
    </PageContainer>
  );
}
