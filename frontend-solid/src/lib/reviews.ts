import { apiDelete, apiGet, apiPost } from "./api";

export type ReviewVote = "helpful" | "unhelpful";

export interface ReviewItemV1 {
  id: string;
  user_id: string | null;
  cafe_id: string;
  rating: number;
  title: string | null;
  body: string | null;
  noise_rating: number | null;
  wifi_rating: number | null;
  outlet_rating: number | null;
  visited_at: string | null;
  is_verified_visit: boolean;
  reviewer_name: string;
  helpful_count: number;
  unhelpful_count: number;
  my_vote: ReviewVote | null;
  created_at: string;
  updated_at: string;
}

export interface ReviewListPayload {
  items: ReviewItemV1[];
  next_cursor: string | null;
  limit: number;
  total_count: number;
}

export interface CreateReviewPayload {
  rating: number;
  title?: string | null;
  body?: string | null;
}

interface ReviewListOptions {
  cursor?: string | null;
  limit?: number;
}

function buildReviewQuery(options: ReviewListOptions = {}) {
  const params = new URLSearchParams();
  const limit = options.limit ?? 10;
  params.set("limit", String(limit));

  if (options.cursor) {
    params.set("cursor", options.cursor);
  }

  return params.toString();
}

export async function getCafeReviews(cafeId: string, options: ReviewListOptions = {}) {
  const query = buildReviewQuery(options);
  return apiGet<ReviewListPayload>(`/api/v1/cafes/${encodeURIComponent(cafeId)}/reviews?${query}`);
}

export async function createCafeReview(cafeId: string, payload: CreateReviewPayload) {
  return apiPost<ReviewItemV1>(
    `/api/v1/cafes/${encodeURIComponent(cafeId)}/reviews`,
    payload,
    { retries: 0 },
  );
}

export async function deleteCafeReview(reviewId: string) {
  return apiDelete<null>(`/api/v1/reviews/${encodeURIComponent(reviewId)}`, { retries: 0 });
}

export async function setReviewVote(reviewId: string, vote: ReviewVote) {
  return apiPost<null>(
    `/api/v1/reviews/${encodeURIComponent(reviewId)}/vote`,
    { vote },
    { retries: 0 },
  );
}

export async function clearReviewVote(reviewId: string) {
  return apiDelete<null>(`/api/v1/reviews/${encodeURIComponent(reviewId)}/vote`, { retries: 0 });
}
