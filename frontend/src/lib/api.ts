import type { AssessmentConfig, MarkerCountError, Patient, Point, View, ViewInfo, ViewResult } from "./types";

export class ApiError<T = unknown> extends Error {
  constructor(public status: number, public body: T) {
    super(apiMessage(status, body));
  }
}

function apiMessage(status: number, body: unknown): string {
  if (body && typeof body === "object") {
    if ("message" in body) return String(body.message);
    if ("detail" in body && typeof body.detail === "string") return body.detail;
  }
  return `Error ${status}`;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, body);
  return body as T;
}

const json = (data: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(data),
});

export const api = {
  defaults: () => request<AssessmentConfig>("/api/config/defaults"),

  views: () => request<ViewInfo[]>("/api/analysis/views"),

  analyze: (view: View, file: File, config: AssessmentConfig) => {
    const form = new FormData();
    form.append("file", file);
    const params = new URLSearchParams(Object.entries(config).map(([k, v]) => [k, String(v)]));
    return request<ViewResult>(`/api/analysis/${view}?${params}`, { method: "POST", body: form });
  },

  /** Recalcula una vista con puntos ajustados por el evaluador. */
  evaluate: (view: View, landmarks: Record<string, Point>, scale_ratio: number, config: AssessmentConfig) =>
    request<ViewResult>(`/api/analysis/${view}/evaluate`, json({ landmarks, scale_ratio, config })),

  patients: (q = "") => request<Patient[]>(`/api/patients?q=${encodeURIComponent(q)}`),

  createPatient: (data: Omit<Patient, "id" | "created_at">) => request<Patient>("/api/patients", json(data)),
};

export function isMarkerError(e: unknown): e is ApiError<MarkerCountError> {
  return e instanceof ApiError && e.status === 422 && !!e.body && typeof e.body === "object" && "expected" in e.body;
}
