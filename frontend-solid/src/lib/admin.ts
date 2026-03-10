import { apiDelete, apiGet, apiPost, apiPut } from "./api";
import type { CafeSummary } from "./cafes";

interface UsersPayload {
  users: AdminUser[];
}

interface ModeratedCafesPayload {
  cafes: ModeratedCafe[];
}

interface ApiMessage {
  message?: string;
}

export interface AdminUser {
  id: number;
  name: string;
  email: string;
  is_admin: boolean;
  is_confirmed: boolean;
  created_at: string | null;
}

export interface ModeratedCafe {
  id: number;
  name: string;
}

export interface CafeFormPayload {
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
  details: string;
}

export async function getUsers(search = "") {
  const query = search.trim();
  const suffix = query ? `?search=${encodeURIComponent(query)}` : "";
  const payload = await apiGet<UsersPayload | null>(`/api/users${suffix}`);
  return payload?.users ?? [];
}

export async function createCafe(payload: CafeFormPayload) {
  return apiPost<ApiMessage | null>("/api/cafes", payload, { retries: 0 });
}

export async function updateCafe(cafeId: number, payload: CafeFormPayload) {
  return apiPut<ApiMessage | null>(`/api/cafes/${cafeId}`, payload, { retries: 0 });
}

export async function deleteCafe(cafeId: number) {
  return apiDelete<ApiMessage | null>(`/api/cafes/${cafeId}`, { retries: 0 });
}

export async function assignModerator(userId: number, cafeId: number) {
  return apiPost<{ assigned: boolean; message?: string } | null>(
    "/api/moderators",
    {
      user_id: userId,
      cafe_id: cafeId,
    },
    { retries: 0 },
  );
}

export async function getModeratedCafes(userId: number) {
  const payload = await apiGet<ModeratedCafesPayload | null>(`/api/moderators/${userId}`, { retries: 0 });
  return payload?.cafes ?? [];
}

export async function removeModerator(userId: number, cafeId: number) {
  return apiDelete<{ success: boolean } | null>(`/api/moderators/${userId}/${cafeId}`, { retries: 0 });
}

export function toCafeFormPayload(cafe: CafeSummary): CafeFormPayload {
  return {
    name: cafe.name,
    map_url: cafe.map_url,
    img_url: cafe.img_url,
    location: cafe.location,
    has_sockets: cafe.has_sockets,
    has_toilet: cafe.has_toilet,
    has_wifi: cafe.has_wifi,
    can_take_calls: cafe.can_take_calls,
    seats: cafe.seats,
    coffee_price: cafe.coffee_price,
    details: cafe.details || "",
  };
}

export function emptyCafeForm(): CafeFormPayload {
  return {
    name: "",
    map_url: "",
    img_url: "",
    location: "",
    has_sockets: false,
    has_toilet: false,
    has_wifi: false,
    can_take_calls: false,
    seats: "",
    coffee_price: "",
    details: "",
  };
}
