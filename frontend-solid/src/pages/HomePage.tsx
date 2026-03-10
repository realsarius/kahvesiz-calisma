import { A } from "@solidjs/router";
import { For, Show, createResource, createSignal } from "solid-js";
import { useAuth } from "../auth/AuthContext";
import { EmptyState } from "../components/states/EmptyState";
import { ErrorState } from "../components/states/ErrorState";
import { LoadingState } from "../components/states/LoadingState";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { PageContainer } from "../components/ui/PageContainer";
import { ApiRequestError, apiGet } from "../lib/api";

interface CafeSummary {
  id: number;
  name: string;
  location: string;
  has_wifi: boolean;
  has_sockets: boolean;
}

interface CafesPayload {
  cafes: CafeSummary[];
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

async function fetchCafes(search: string) {
  const query = search.trim();
  const suffix = query ? `?search=${encodeURIComponent(query)}` : "";
  const payload = await apiGet<CafesPayload | null>(`/api/cafes${suffix}`);
  return payload?.cafes ?? [];
}

export default function HomePage() {
  const auth = useAuth();
  const [searchDraft, setSearchDraft] = createSignal("");
  const [search, setSearch] = createSignal("");
  const [cafes, { refetch }] = createResource(search, fetchCafes);

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
    <PageContainer
      title="Kafe rehberi"
      subtitle="Liste verisi Flask API uzerinden yuklenir. Session ve CSRF davranisi merkezi API katmanindan yonetilir."
    >
      <Show when={auth.state.sessionExpired}>
        <Alert variant="warning" title="Oturum kapandi">
          Oturumunuz sonlandi. Write islemleri icin yeniden <A href="/login">login</A> olmaniz gerekir.
        </Alert>
      </Show>

      <div class="grid-two-columns">
        <Card title="Kafe listesi" description="Public endpoint: GET /api/cafes">
          <form class="search-form" onSubmit={onSearchSubmit}>
            <Input
              id="search-cafe"
              label="Kafe ara"
              value={searchDraft()}
              onInput={(event) => setSearchDraft(event.currentTarget.value)}
              placeholder="Ornek: Kadikoy"
              hint="Arama backend search parametresine gonderilir."
            />
            <div class="row-actions">
              <Button type="submit">Ara</Button>
              <Button type="button" variant="secondary" onClick={clearSearch}>
                Temizle
              </Button>
            </div>
          </form>

          <Show
            when={!cafes.loading}
            fallback={<LoadingState title="Kafeler yukleniyor" description="Liste aliniyor..." />}
          >
            <Show
              when={!cafes.error}
              fallback={
                <ErrorState
                  title="Kafe listesi yuklenemedi"
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
                    title="Kafe bulunamadi"
                    description="Filtreyi temizleyip tekrar deneyebilirsiniz."
                    actionLabel="Filtreyi sifirla"
                    onAction={clearSearch}
                  />
                }
              >
                <ul class="cafe-list">
                  <For each={cafes() ?? []}>
                    {(cafe) => (
                      <li class="cafe-list__item">
                        <div>
                          <p class="cafe-list__name">{cafe.name}</p>
                          <p class="cafe-list__meta">{cafe.location}</p>
                        </div>
                        <div class="chip-row">
                          <span class="ui-chip">wifi: {cafe.has_wifi ? "var" : "yok"}</span>
                          <span class="ui-chip">priz: {cafe.has_sockets ? "var" : "yok"}</span>
                        </div>
                      </li>
                    )}
                  </For>
                </ul>
              </Show>
            </Show>
          </Show>
        </Card>

        <Card title="Auth bootstrap" description="Context state anlik gorunum">
          <dl class="meta-list">
            <div>
              <dt>loading</dt>
              <dd>{String(auth.state.loading)}</dd>
            </div>
            <div>
              <dt>isAuthenticated</dt>
              <dd>{String(auth.state.isAuthenticated)}</dd>
            </div>
            <div>
              <dt>sessionExpired</dt>
              <dd>{String(auth.state.sessionExpired)}</dd>
            </div>
            <div>
              <dt>user</dt>
              <dd>{auth.state.user ? auth.state.user.email : "null"}</dd>
            </div>
          </dl>
        </Card>
      </div>
    </PageContainer>
  );
}
