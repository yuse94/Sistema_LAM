import type { AssessmentConfig, MarkerCountError, Patient, View, ViewResult } from "./types";

export class ApiError<T = unknown> extends Error {
  constructor(public status: number, public body: T) {
    super(typeof body === "object" && body && "message" in body ? String(body.message) : `Error ${status}`);
  }
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, body);
  return body as T;
}

export const api = {
  defaults: () => request<AssessmentConfig>("/api/config/defaults"),

  analyze: (view: View, file: File, config: AssessmentConfig) => {
    const form = new FormData();
    form.append("file", file);
    const params = new URLSearchParams(Object.entries(config).map(([k, v]) => [k, String(v)]));
    return request<ViewResult>(`/api/analysis/${view}?${params}`, { method: "POST", body: form });
  },

  patients: (q = "") => request<Patient[]>(`/api/patients?q=${encodeURIComponent(q)}`),

  createPatient: (data: Omit<Patient, "id" | "created_at">) =>
    request<Patient>("/api/patients", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),
};

export function isMarkerError(e: unknown): e is ApiError<MarkerCountError> {
  return e instanceof ApiError && e.status === 422 && !!e.body && typeof e.body === "object" && "expected" in e.body;
}
