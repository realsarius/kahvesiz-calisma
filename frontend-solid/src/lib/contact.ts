import { apiPost } from "./api";

interface ContactApiResponse {
  message?: string;
}

export interface ContactPayload {
  email: string;
  subject: string;
  message: string;
}

export async function sendContactMessage(payload: ContactPayload) {
  return apiPost<ContactApiResponse>("/api/contact", payload, {
    retries: 0,
    timeoutMs: 10_000,
    emitAuthEvent: false,
  });
}
