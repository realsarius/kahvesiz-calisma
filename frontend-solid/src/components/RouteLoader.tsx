import { LoadingState } from "./states/LoadingState";

export function RouteLoader() {
  return <LoadingState title="Sayfa yükleniyor" description="Rota içeriği hazırlanıyor." />;
}
