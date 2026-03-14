import { type Accessor, createEffect, createMemo, createResource, createSignal } from "solid-js";
import { apiGet } from "./api";

export interface CafeSummary {
  id: string;
  name: string;
  map_url: string | null;
  img_url: string | null;
  location: string | null;
  has_sockets: boolean;
  has_toilet: boolean;
  has_wifi: boolean;
  can_take_calls: boolean;
  seats: string | null;
  coffee_price: string | null;
  details: string | null;
  created_at: string;
  updated_at: string;
  slug: string;
}

interface CafesPayload {
  cafes: CafeSummary[];
}
export interface CafeListFilters {
  neighborhood?: string;
  wifi?: boolean | null;
  noiseLevel?: string;
  hasOutlet?: boolean | null;
  limit?: number;
}

export interface CafeListItemV1 {
  id: string;
  name: string;
  slug: string;
  address: string;
  latitude: number;
  longitude: number;
  avg_rating: number;
  review_count: number;
  neighborhood: string | null;
  neighborhood_slug: string | null;
  wifi_available: boolean;
  noise_level: string | null;
  created_at: string;
}

interface CafesV1ListPayload {
  items: CafeListItemV1[];
  next_cursor: string | null;
  limit: number;
  total_count: number;
}

export interface CafeDetailV1 {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  address: string;
  latitude: number;
  longitude: number;
  phone: string | null;
  website: string | null;
  instagram: string | null;
  google_maps_url: string | null;
  is_verified: boolean;
  is_active: boolean;
  status: string;
  total_capacity: number | null;
  indoor_capacity: number | null;
  outdoor_capacity: number | null;
  avg_rating: number;
  review_count: number;
  neighborhood: string | null;
  neighborhood_slug: string | null;
  amenities: {
    wifi_available: boolean;
    wifi_speed_mbps: number | null;
    outlet_count: number | null;
    outlet_accessibility: string | null;
    noise_level: string | null;
    has_natural_light: boolean;
    has_ac: boolean;
    has_heating: boolean;
    has_parking: boolean;
    has_accessible_entry: boolean;
    allows_laptop: boolean;
    min_spend_try: number | null;
    has_food: boolean;
    has_alcohol: boolean;
    pet_friendly: boolean;
  };
  hours: Array<{
    day_of_week: number;
    opens_at: string | null;
    closes_at: string | null;
    is_closed: boolean;
  }>;
  images: Array<{
    url: string;
    alt_text: string | null;
    is_primary: boolean;
    sort_order: number;
  }>;
  seats: Array<{
    seat_type: string;
    total_count: number;
    available_count: number;
    has_outlet: boolean;
    notes: string | null;
  }>;
  reviews: Array<{
    id: string;
    rating: number;
    title: string | null;
    body: string | null;
    reviewer_name: string;
    visited_at: string | null;
    created_at: string;
  }>;
  created_at: string;
  updated_at: string;
}

function buildV1ListQuery(filters: CafeListFilters, cursor: string | null) {
  const params = new URLSearchParams();
  params.set("limit", String(filters.limit ?? 20));

  const neighborhood = (filters.neighborhood ?? "").trim();
  if (neighborhood) {
    params.set("neighborhood", neighborhood.toLowerCase());
  }

  if (typeof filters.wifi === "boolean") {
    params.set("wifi", filters.wifi ? "true" : "false");
  }

  const noiseLevel = (filters.noiseLevel ?? "").trim();
  if (noiseLevel) {
    params.set("noise_level", noiseLevel.toLowerCase());
  }

  if (typeof filters.hasOutlet === "boolean") {
    params.set("has_outlet", filters.hasOutlet ? "true" : "false");
  }

  if (cursor) {
    params.set("cursor", cursor);
  }

  return params.toString();
}

export async function getCafes(search = "") {
  const query = search.trim();
  const params = new URLSearchParams();
  if (query) {
    params.set("search", query);
  }
  const suffix = params.toString() ? `?${params.toString()}` : "";
  const payload = await apiGet<CafesPayload | null>(`/api/v1/admin/cafes${suffix}`);
  return payload?.cafes ?? [];
}

export async function getCafeById(id: number) {
  const payload = await apiGet<CafeSummary | null>(`/api/cafes/${id}`);
  return payload;
}

export async function getCafesPageV1(filters: CafeListFilters, cursor: string | null = null) {
  const query = buildV1ListQuery(filters, cursor);
  return apiGet<CafesV1ListPayload>(`/api/v1/cafes?${query}`);
}

export async function getCafeBySlug(slug: string) {
  const safeSlug = (slug ?? "").trim();
  return apiGet<CafeDetailV1>(`/api/v1/cafes/${encodeURIComponent(safeSlug)}`);
}

function mergeCafeItems(previous: CafeListItemV1[], incoming: CafeListItemV1[]) {
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

export function useInfiniteCafes(filters: Accessor<CafeListFilters>) {
  const normalizedFilters = createMemo<CafeListFilters>(() => ({
    neighborhood: (filters().neighborhood ?? "").trim(),
    wifi: filters().wifi ?? null,
    noiseLevel: (filters().noiseLevel ?? "").trim(),
    hasOutlet: filters().hasOutlet ?? null,
    limit: filters().limit ?? 20,
  }));

  const [cursor, setCursor] = createSignal<string | null>(null);
  const [items, setItems] = createSignal<CafeListItemV1[]>([]);
  const [nextCursor, setNextCursor] = createSignal<string | null>(null);
  const [totalCount, setTotalCount] = createSignal(0);
  const [loadedOnce, setLoadedOnce] = createSignal(false);

  createEffect(() => {
    normalizedFilters();
    setCursor(null);
    setItems([]);
    setNextCursor(null);
    setTotalCount(0);
    setLoadedOnce(false);
  });

  const [page, { refetch }] = createResource(
    createMemo(() => ({
      filters: normalizedFilters(),
      cursor: cursor(),
    })),
    async (source) => getCafesPageV1(source.filters, source.cursor),
  );

  createEffect(() => {
    const payload = page();
    if (!payload) {
      return;
    }

    if (cursor() === null) {
      setItems(payload.items);
    } else {
      setItems((previous) => mergeCafeItems(previous, payload.items));
    }

    setNextCursor(payload.next_cursor ?? null);
    setTotalCount(payload.total_count ?? 0);
    setLoadedOnce(true);
  });

  const hasMore = createMemo(() => Boolean(nextCursor()));
  const isLoadingInitial = createMemo(() => page.loading && !loadedOnce());
  const isLoadingMore = createMemo(() => page.loading && loadedOnce() && cursor() !== null);

  const loadMore = () => {
    if (page.loading) {
      return;
    }
    const next = nextCursor();
    if (!next) {
      return;
    }
    setCursor(next);
  };

  const retry = () => {
    void refetch();
  };

  return {
    items,
    totalCount,
    hasMore,
    isLoadingInitial,
    isLoadingMore,
    error: () => page.error,
    loadMore,
    retry,
  };
}
