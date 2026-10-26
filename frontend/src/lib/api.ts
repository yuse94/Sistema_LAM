import type {
  AssessmentConfig,
  Calibration,
  MarkerCountError,
  Patient,
  Point,
  PosePoint,
  VerticalLine,
  View,
  ViewInfo,
  ViewResult,
} from "./types";

export class ApiError<T = unknown> extends Error {
  constructor(public status: number, public body: T) {
    super(apiMessage(status, body));
  }
}

function apiMessage(status: number, body: unknown): string {
  if (body && typeof body === "object") {
    if ("message" in body) return String(body.message);
    if ("detail" in body) {
      const detail = body.detail;
      if (typeof detail === "string") return detail;
      // Errores de validación de FastAPI: lista de {msg, loc}
      if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg);
    }
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

/** Datos para recalcular una vista. La escala va directa (con marcadores) o por estatura. */
export interface EvaluateRequest {
  landmarks: Record<string, Point>;
  scale_ratio?: number;
  height_cm?: number;
  calibration?: Calibration | null;
  vertical_line?: VerticalLine | null;
  config: AssessmentConfig;
}

export interface PoseRequest {
  pose: PosePoint[];
  height_cm: number;
  calibration?: Calibration | null;
  vertical_line?: VerticalLine | null;
  config: AssessmentConfig;
}

export const api = {
  defaults: () => request<AssessmentConfig>("/api/config/defaults"),

  views: () => request<ViewInfo[]>("/api/analysis/views"),

  /** Modo con marcadores verdes: se sube la foto. */
  analyze: (view: View, file: File, config: AssessmentConfig) => {
    const form = new FormData();
    form.append("file", file);
    const params = new URLSearchParams(Object.entries(config).map(([k, v]) => [k, String(v)]));
    return request<ViewResult>(`/api/analysis/${view}?${params}`, { method: "POST", body: form });
  },

  /** Modo sin marcadores: se envían los puntos de MediaPipe y la estatura. */
  pose: (view: View, data: PoseRequest) => request<ViewResult>(`/api/analysis/${view}/pose`, json(data)),

  /** Recalcula una vista con puntos ajustados por el evaluador. */
  evaluate: (view: View, data: EvaluateRequest) =>
    request<ViewResult>(`/api/analysis/${view}/evaluate`, json(data)),

  patients: (q = "") => request<Patient[]>(`/api/patients?q=${encodeURIComponent(q)}`),

  createPatient: (data: Omit<Patient, "id" | "created_at">) => request<Patient>("/api/patients", json(data)),
};

export function isMarkerError(e: unknown): e is ApiError<MarkerCountError> {
  return e instanceof ApiError && e.status === 422 && !!e.body && typeof e.body === "object" && "expected" in e.body;
}
