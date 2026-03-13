import { For, Show, createMemo, createResource, createSignal } from "solid-js";
import { createStore } from "solid-js/store";
import { useAuth } from "../auth/AuthContext";
import { EmptyState } from "../components/states/EmptyState";
import { ErrorState } from "../components/states/ErrorState";
import { LoadingState } from "../components/states/LoadingState";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { PageContainer } from "../components/ui/PageContainer";
import { ApiRequestError } from "../lib/api";
import { getCafes } from "../lib/cafes";
import {
  assignModerator,
  createCafe,
  deleteCafe,
  emptyCafeForm,
  getModeratedCafes,
  getUsers,
  removeModerator,
  toCafeFormPayload,
  updateCafe,
  type CafeFormPayload,
} from "../lib/admin";

function toErrorMessage(error: unknown) {
  if (error instanceof ApiRequestError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Beklenmeyen bir hata oluştu.";
}

export default function AdminPage() {
  const auth = useAuth();

  const [refreshKey, setRefreshKey] = createSignal(0);
  const [searchDraft, setSearchDraft] = createSignal("");
  const [searchQuery, setSearchQuery] = createSignal("");

  const [editingCafeId, setEditingCafeId] = createSignal<number | null>(null);
  const [submittingCafe, setSubmittingCafe] = createSignal(false);
  const [busyCafeId, setBusyCafeId] = createSignal<number | null>(null);

  const [selectedUserId, setSelectedUserId] = createSignal<number | null>(null);
  const [selectedCafeId, setSelectedCafeId] = createSignal<number | null>(null);
  const [assigningModerator, setAssigningModerator] = createSignal(false);

  const [feedbackError, setFeedbackError] = createSignal<string | null>(null);
  const [feedbackSuccess, setFeedbackSuccess] = createSignal<string | null>(null);

  const [cafeForm, setCafeForm] = createStore<CafeFormPayload>(emptyCafeForm());

  const [cafes, { refetch: refetchCafes }] = createResource(
    () => [searchQuery(), refreshKey()] as const,
    ([search]) => getCafes(search),
  );
  const [users, { refetch: refetchUsers }] = createResource(
    () => refreshKey(),
    () => getUsers(),
  );

  const [moderatedCafes, { refetch: refetchModeratedCafes }] = createResource(
    () => [selectedUserId(), refreshKey()] as const,
    async ([userId]) => {
      if (!userId) {
        return [];
      }
      return getModeratedCafes(userId);
    },
  );

  const isAdmin = createMemo(() => Boolean(auth.state.user?.isAdmin));

  const resetFeedback = () => {
    setFeedbackError(null);
    setFeedbackSuccess(null);
  };

  const resetCafeForm = () => {
    setEditingCafeId(null);
    setCafeForm(emptyCafeForm());
  };

  const reloadAll = () => {
    setRefreshKey((value) => value + 1);
    void refetchCafes();
    void refetchUsers();
    if (selectedUserId()) {
      void refetchModeratedCafes();
    }
  };

  const onSearchSubmit = (event: SubmitEvent) => {
    event.preventDefault();
    setSearchQuery(searchDraft());
  };

  const clearSearch = () => {
    setSearchDraft("");
    setSearchQuery("");
  };

  const onCafeSubmit = async (event: SubmitEvent) => {
    event.preventDefault();
    resetFeedback();

    if (
      !cafeForm.name.trim() ||
      !cafeForm.map_url.trim() ||
      !cafeForm.img_url.trim() ||
      !cafeForm.location.trim() ||
      !cafeForm.seats.trim() ||
      !cafeForm.coffee_price.trim()
    ) {
      setFeedbackError("Kafe formundaki zorunlu alanlar boş bırakılamaz.");
      return;
    }

    setSubmittingCafe(true);
    try {
      if (editingCafeId()) {
        await updateCafe(editingCafeId() as number, cafeForm);
        setFeedbackSuccess("Kafe başarıyla güncellendi.");
      } else {
        await createCafe(cafeForm);
        setFeedbackSuccess("Kafe başarıyla eklendi.");
      }

      resetCafeForm();
      reloadAll();
    } catch (error) {
      setFeedbackError(toErrorMessage(error));
    } finally {
      setSubmittingCafe(false);
    }
  };

  const startCafeEdit = (id: number) => {
    const target = (cafes() ?? []).find((item) => item.id === id);
    if (!target) {
      return;
    }

    setEditingCafeId(id);
    setCafeForm(toCafeFormPayload(target));
    resetFeedback();
  };

  const onDeleteCafe = async (id: number) => {
    if (!window.confirm("Bu kafeyi silmek istediğinizden emin misiniz?")) {
      return;
    }

    resetFeedback();
    setBusyCafeId(id);
    try {
      await deleteCafe(id);
      setFeedbackSuccess("Kafe silindi.");
      if (editingCafeId() === id) {
        resetCafeForm();
      }
      reloadAll();
    } catch (error) {
      setFeedbackError(toErrorMessage(error));
    } finally {
      setBusyCafeId(null);
    }
  };

  const onAssignModerator = async () => {
    resetFeedback();

    if (!selectedUserId() || !selectedCafeId()) {
      setFeedbackError("Moderatör atamak için kullanıcı ve kafe seçilmelidir.");
      return;
    }

    setAssigningModerator(true);
    try {
      const response = await assignModerator(selectedUserId() as number, selectedCafeId() as number);
      setFeedbackSuccess(response?.message || "Moderatör atama işlemi tamamlandı.");
      setSelectedCafeId(null);
      reloadAll();
    } catch (error) {
      setFeedbackError(toErrorMessage(error));
    } finally {
      setAssigningModerator(false);
    }
  };

  const onRemoveModerator = async (cafeId: number) => {
    const userId = selectedUserId();
    if (!userId) {
      return;
    }

    resetFeedback();
    try {
      await removeModerator(userId, cafeId);
      setFeedbackSuccess("Moderatör ataması kaldırıldı.");
      reloadAll();
    } catch (error) {
      setFeedbackError(toErrorMessage(error));
    }
  };

  if (auth.state.loading) {
    return <LoadingState title="Admin paneli yükleniyor" />;
  }

  if (!auth.state.isAuthenticated) {
    return (
      <PageContainer title="Admin" subtitle="Bu alana erişim için giriş yapmalısınız.">
        <ErrorState
          title="Kimlik doğrulama gerekli"
          description="Admin paneline erişmek için aktif bir oturum gereklidir."
        />
      </PageContainer>
    );
  }

  if (!isAdmin()) {
    return (
      <PageContainer title="Admin" subtitle="Rol tabanlı erişim kontrolü uygulanır.">
        <ErrorState title="Yetkisiz erişim" description="Bu alana sadece admin kullanıcılar erişebilir." />
      </PageContainer>
    );
  }

  return (
    <PageContainer
      title="Admin paneli"
      subtitle="Kafe yönetimi ve moderatör atama akışları"
      actions={
        <Button variant="secondary" onClick={reloadAll}>
          Verileri yenile
        </Button>
      }
    >
      <Show when={feedbackError()}>{(value) => <Alert variant="error">{value()}</Alert>}</Show>
      <Show when={feedbackSuccess()}>{(value) => <Alert variant="success">{value()}</Alert>}</Show>

      <div class="admin-grid">
        <Card
          title={editingCafeId() ? `Kafe düzenle (#${editingCafeId()})` : "Yeni kafe ekle"}
          description="Kafe CRUD işlemleri"
        >
          <form class="stack-form" onSubmit={onCafeSubmit}>
            <Input
              id="admin-cafe-name"
              label="Kafe adı"
              value={cafeForm.name}
              onInput={(event) => setCafeForm("name", event.currentTarget.value)}
            />
            <Input
              id="admin-map-url"
              label="Harita URL"
              value={cafeForm.map_url}
              onInput={(event) => setCafeForm("map_url", event.currentTarget.value)}
            />
            <Input
              id="admin-img-url"
              label="Görsel URL"
              value={cafeForm.img_url}
              onInput={(event) => setCafeForm("img_url", event.currentTarget.value)}
            />
            <Input
              id="admin-location"
              label="Konum"
              value={cafeForm.location}
              onInput={(event) => setCafeForm("location", event.currentTarget.value)}
            />

            <div class="grid-two-columns">
              <Input
                id="admin-seats"
                label="Koltuk"
                value={cafeForm.seats}
                onInput={(event) => setCafeForm("seats", event.currentTarget.value)}
              />
              <Input
                id="admin-coffee-price"
                label="Kahve fiyatı"
                value={cafeForm.coffee_price}
                onInput={(event) => setCafeForm("coffee_price", event.currentTarget.value)}
              />
            </div>

            <div class="flag-group">
              <label class="flag-item">
                <input
                  type="checkbox"
                  checked={cafeForm.has_wifi}
                  onChange={(event) => setCafeForm("has_wifi", event.currentTarget.checked)}
                />
                Wi-Fi var
              </label>
              <label class="flag-item">
                <input
                  type="checkbox"
                  checked={cafeForm.has_sockets}
                  onChange={(event) => setCafeForm("has_sockets", event.currentTarget.checked)}
                />
                Priz var
              </label>
              <label class="flag-item">
                <input
                  type="checkbox"
                  checked={cafeForm.has_toilet}
                  onChange={(event) => setCafeForm("has_toilet", event.currentTarget.checked)}
                />
                Tuvalet var
              </label>
              <label class="flag-item">
                <input
                  type="checkbox"
                  checked={cafeForm.can_take_calls}
                  onChange={(event) => setCafeForm("can_take_calls", event.currentTarget.checked)}
                />
                Çağrı uygun
              </label>
            </div>

            <div class="ui-field">
              <label class="ui-field__label" for="admin-details">
                Detay
              </label>
              <textarea
                id="admin-details"
                class="ui-input ui-textarea"
                value={cafeForm.details}
                onInput={(event) => setCafeForm("details", event.currentTarget.value)}
                placeholder="Kafe detay bilgisi"
              />
            </div>

            <div class="row-actions">
              <Button type="submit" disabled={submittingCafe()}>
                {submittingCafe()
                  ? "Kaydediliyor..."
                  : editingCafeId()
                    ? "Kafe güncelle"
                    : "Kafe ekle"}
              </Button>
              <Button type="button" variant="ghost" onClick={resetCafeForm}>
                Formu sıfırla
              </Button>
            </div>
          </form>
        </Card>

        <Card title="Kafe listesi" description="Seçili kayıt düzenlenebilir veya silinebilir">
          <form class="search-form" onSubmit={onSearchSubmit}>
            <Input
              id="admin-cafe-search"
              label="Listede ara"
              value={searchDraft()}
              onInput={(event) => setSearchDraft(event.currentTarget.value)}
              placeholder="Kafe adı veya konum"
            />
            <div class="row-actions">
              <Button type="submit" size="sm">
                Ara
              </Button>
              <Button type="button" size="sm" variant="secondary" onClick={clearSearch}>
                Temizle
              </Button>
            </div>
          </form>

          <Show when={!cafes.loading} fallback={<LoadingState title="Kafe listesi yükleniyor" />}>
            <Show
              when={!cafes.error}
              fallback={
                <ErrorState
                  title="Kafe listesi alınamadı"
                  description={toErrorMessage(cafes.error)}
                  actionLabel="Tekrar dene"
                  onAction={() => void refetchCafes()}
                />
              }
            >
              <Show when={(cafes() ?? []).length > 0} fallback={<EmptyState title="Kafe bulunamadı" />}>
                <ul class="admin-list">
                  <For each={cafes() ?? []}>
                    {(cafe) => (
                      <li class="admin-list__row">
                        <div>
                          <p class="admin-list__title">{cafe.name}</p>
                          <p class="admin-list__meta">{cafe.location}</p>
                        </div>
                        <div class="row-actions">
                          <Button type="button" size="sm" variant="secondary" onClick={() => startCafeEdit(cafe.id)}>
                            Düzenle
                          </Button>
                          <Button
                            type="button"
                            size="sm"
                            variant="danger"
                            disabled={busyCafeId() === cafe.id}
                            onClick={() => void onDeleteCafe(cafe.id)}
                          >
                            {busyCafeId() === cafe.id ? "Siliniyor..." : "Sil"}
                          </Button>
                        </div>
                      </li>
                    )}
                  </For>
                </ul>
              </Show>
            </Show>
          </Show>
        </Card>
      </div>

      <div class="admin-grid">
        <Card title="Moderatör atama" description="Kullanıcıyı seçili kafeye moderatör olarak ata">
          <div class="stack-form">
            <div class="ui-field">
              <label class="ui-field__label" for="moderator-user">
                Kullanıcı
              </label>
              <select
                id="moderator-user"
                class="ui-input ui-select"
                value={selectedUserId() ?? ""}
                onChange={(event) => setSelectedUserId(Number.parseInt(event.currentTarget.value, 10) || null)}
              >
                <option value="">Kullanıcı seçin</option>
                <For each={users() ?? []}>
                  {(user) => (
                    <option value={user.id}>{`${user.name} (${user.email})`}</option>
                  )}
                </For>
              </select>
            </div>

            <div class="ui-field">
              <label class="ui-field__label" for="moderator-cafe">
                Kafe
              </label>
              <select
                id="moderator-cafe"
                class="ui-input ui-select"
                value={selectedCafeId() ?? ""}
                onChange={(event) => setSelectedCafeId(Number.parseInt(event.currentTarget.value, 10) || null)}
              >
                <option value="">Kafe seçin</option>
                <For each={cafes() ?? []}>{(cafe) => <option value={cafe.id}>{cafe.name}</option>}</For>
              </select>
            </div>

            <Button type="button" disabled={assigningModerator()} onClick={() => void onAssignModerator()}>
              {assigningModerator() ? "Atanıyor..." : "Moderatör ata"}
            </Button>
          </div>
        </Card>

        <Card title="Moderatör atama listesi" description="Seçili kullanıcının moderatör olduğu kafeler">
          <Show when={!users.loading} fallback={<LoadingState title="Kullanıcılar yükleniyor" />}>
            <Show
              when={!users.error}
              fallback={
                <ErrorState
                  title="Kullanıcılar alınamadı"
                  description={toErrorMessage(users.error)}
                  actionLabel="Tekrar dene"
                  onAction={() => void refetchUsers()}
                />
              }
            >
              <Show when={selectedUserId()} fallback={<EmptyState title="Bir kullanıcı seçin" />}>
                <Show when={!moderatedCafes.loading} fallback={<LoadingState title="Moderatör kayıtları yükleniyor" />}>
                  <Show
                    when={!moderatedCafes.error}
                    fallback={
                      <ErrorState
                        title="Moderatör kayıtları alınamadı"
                        description={toErrorMessage(moderatedCafes.error)}
                        actionLabel="Tekrar dene"
                        onAction={() => void refetchModeratedCafes()}
                      />
                    }
                  >
                    <Show
                      when={(moderatedCafes() ?? []).length > 0}
                      fallback={<EmptyState title="Bu kullanıcıya ait moderatör kaydı yok" />}
                    >
                      <ul class="admin-list">
                        <For each={moderatedCafes() ?? []}>
                          {(item) => (
                            <li class="admin-list__row">
                              <p class="admin-list__title">{item.name}</p>
                              <Button
                                type="button"
                                size="sm"
                                variant="danger"
                                onClick={() => void onRemoveModerator(item.id)}
                              >
                                Kaldır
                              </Button>
                            </li>
                          )}
                        </For>
                      </ul>
                    </Show>
                  </Show>
                </Show>
              </Show>
            </Show>
          </Show>
        </Card>
      </div>

      <Card title="Kullanıcılar" description="Rol bazlı görünürlük doğrulaması">
        <Show when={!users.loading} fallback={<LoadingState title="Kullanıcılar yükleniyor" />}>
          <Show
            when={!users.error}
            fallback={
              <ErrorState
                title="Kullanıcılar alınamadı"
                description={toErrorMessage(users.error)}
                actionLabel="Tekrar dene"
                onAction={() => void refetchUsers()}
              />
            }
          >
            <Show when={(users() ?? []).length > 0} fallback={<EmptyState title="Kullanıcı bulunamadı" />}>
              <ul class="admin-list">
                <For each={users() ?? []}>
                  {(user) => (
                    <li class="admin-list__row">
                      <div>
                        <p class="admin-list__title">{user.name}</p>
                        <p class="admin-list__meta">{user.email}</p>
                      </div>
                      <div class="chip-row">
                        <span class="ui-chip">{user.is_admin ? "admin" : "user"}</span>
                        <span class="ui-chip">{user.is_confirmed ? "confirmed" : "pending"}</span>
                      </div>
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
