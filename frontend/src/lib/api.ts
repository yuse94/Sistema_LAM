import type {
  AssessmentConfig,
  Calibration,
  Evaluation,
  EvaluationCreate,
  EvaluationUpdate,
  EvaluationSummary,
  History,
  MarkerCountError,
  Patient,
  PatientInput,
  PatientListItem,
  Point,
  PointInfo,
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
  if (res.status === 204) return undefined as T;
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

  /** Diccionario de puntos anatómicos. */
  points: () => request<PointInfo[]>("/api/points"),

  patients: (q = "") => request<PatientListItem[]>(`/api/patients?q=${encodeURIComponent(q)}`),

  patient: (id: number) => request<Patient>(`/api/patients/${id}`),

  createPatient: (data: PatientInput) => request<Patient>("/api/patients", json(data)),

  updatePatient: (id: number, data: PatientInput) =>
    request<Patient>(`/api/patients/${id}`, { ...json(data), method: "PUT" }),

  /** Elimina al paciente con todas sus evaluaciones y fotografías. */
  deletePatient: (id: number) => request<void>(`/api/patients/${id}`, { method: "DELETE" }),

  history: (patientId: number, view: View) => request<History>(`/api/patients/${patientId}/history?view=${view}`),

  /** Guarda la evaluación: una foto por vista, en el mismo orden que data.views. */
  saveEvaluation: (data: EvaluationCreate, images: Blob[]) => {
    const form = new FormData();
    form.append("data", JSON.stringify(data));
    images.forEach((img, i) => form.append("images", img, `${data.views[i].view}.jpg`));
    return request<Evaluation>("/api/evaluations", { method: "POST", body: form });
  },

  /** Corrige una evaluación guardada (puntos, estatura u observaciones); el servidor vuelve a evaluar. */
  updateEvaluation: (id: number, data: EvaluationUpdate) =>
    request<Evaluation>(`/api/evaluations/${id}`, { ...json(data), method: "PUT" }),

  evaluations: (patientId: number) => request<EvaluationSummary[]>(`/api/evaluations?patient_id=${patientId}`),

  evaluation: (id: number) => request<Evaluation>(`/api/evaluations/${id}`),

  deleteEvaluation: (id: number) => request<void>(`/api/evaluations/${id}`, { method: "DELETE" }),
};

/** Enlaces directos (descargas): los abre el navegador. */
export const links = {
  report: (id: number, download = false) => `/api/evaluations/${id}/report.pdf${download ? "?download=true" : ""}`,
  excel: (patientId?: number) => `/api/evaluations/export.xlsx${patientId ? `?patient_id=${patientId}` : ""}`,
};

export function isMarkerError(e: unknown): e is ApiError<MarkerCountError> {
  return e instanceof ApiError && e.status === 422 && !!e.body && typeof e.body === "object" && "expected" in e.body;
}
