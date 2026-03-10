import { A } from "@solidjs/router";
import { For, Show, createResource } from "solid-js";
import { useAuth } from "../auth/AuthContext";
import { EmptyState } from "../components/states/EmptyState";
import { ErrorState } from "../components/states/ErrorState";
import { LoadingState } from "../components/states/LoadingState";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { PageContainer } from "../components/ui/PageContainer";
import { ApiRequestError } from "../lib/api";
import { getCafes } from "../lib/cafes";

const highlights = [
  "Session/cookie tabanli auth davranisi korunur",
  "CSRF korumali write endpoint semantigi bozulmaz",
  "Public ekranlar API envelope sozlesmesine sadik kalir",
];

function readErrorMessage(error: unknown) {
  if (error instanceof ApiRequestError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Bilinmeyen hata";
}

export default function HomePage() {
  const auth = useAuth();
  const [previewCafes, { refetch }] = createResource(() => "", getCafes);

  return (
    <PageContainer
      title="Kahvesiz Calisma"
      subtitle="SolidJS public yuzeyi Flask API ile uyumlu sekilde kademeli tasiniyor."
      actions={
        <>
          <Button variant="secondary" onClick={() => void refetch()}>
            Listeyi yenile
          </Button>
          <A class="ui-button ui-button--primary ui-button--md" href="/cafes">
            Kafelere git
          </A>
        </>
      }
    >
      <Show when={auth.state.sessionExpired}>
        <Alert variant="warning" title="Oturum kapandi">
          Oturum suresi doldu. Yetkili islemler icin yeniden <A class="ui-link" href="/login">login</A> olabilirsiniz.
        </Alert>
      </Show>

      <div class="grid-three-columns">
        <Card title="Yol haritasi" description="Frontend gecisi temel ilkeler">
          <ul class="simple-list">
            <For each={highlights}>{(item) => <li>{item}</li>}</For>
          </ul>
        </Card>

        <Card title="Hizli baglantilar" description="Public sayfalar">
          <div class="stack-links">
            <A class="ui-link" href="/cafes">
              Cafes listesi
            </A>
            <A class="ui-link" href="/about">
              Hakkinda
            </A>
            <A class="ui-link" href="/privacy">
              Gizlilik politikasi
            </A>
            <A class="ui-link" href="/license">
              Lisans
            </A>
            <A class="ui-link" href="/contact">
              Iletisim
            </A>
          </div>
        </Card>

        <Card title="Auth durumu" description="Bootstrap context durumu">
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

      <Card title="One cikan kafeler" description="/api/cafes endpointinden ilk 4 kayit">
        <Show when={!previewCafes.loading} fallback={<LoadingState title="Kafe onizlemesi yukleniyor" />}>
          <Show
            when={!previewCafes.error}
            fallback={
              <ErrorState
                title="Kafe onizlemesi alinamadi"
                description={readErrorMessage(previewCafes.error)}
                actionLabel="Tekrar dene"
                onAction={() => void refetch()}
              />
            }
          >
            <Show
              when={(previewCafes() ?? []).length > 0}
              fallback={<EmptyState title="Henuz kafe bulunmuyor" description="Veri eklendiginde burada listelenecek." />}
            >
              <ul class="cafe-list">
                <For each={(previewCafes() ?? []).slice(0, 4)}>
                  {(cafe) => (
                    <li class="cafe-list__item">
                      <div>
                        <A class="cafe-list__name-link" href={`/cafes/${cafe.id}`}>
                          {cafe.name}
                        </A>
                        <p class="cafe-list__meta">{cafe.location}</p>
                      </div>
                      <span class="ui-chip">{cafe.coffee_price || "fiyat yok"}</span>
                    </li>
                  )}
                </For>
              </ul>
            </Show>
          </Show>
        </Show>
      </Card>
    </PageContainer>
  );
}
