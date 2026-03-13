import { apiGet } from "./api";

export interface CafeSummary {
  id: number;
  name: string;
  map_url: string;
  img_url: string;
  location: string;
  has_sockets: boolean;
  has_toilet: boolean;
  has_wifi: boolean;
  can_take_calls: boolean;
  seats: string;
  coffee_price: string;
  details: string | null;
}

interface CafesPayload {
  cafes: CafeSummary[];
}

export async function getCafes(search = "") {
  const query = search.trim();
  const suffix = query ? `?search=${encodeURIComponent(query)}` : "";
  const payload = await apiGet<CafesPayload | null>(`/api/cafes${suffix}`);
  return payload?.cafes ?? [];
}

export async function getCafeById(id: number) {
  const payload = await apiGet<CafeSummary | null>(`/api/cafes/${id}`);
  return payload;
}
