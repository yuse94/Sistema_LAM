// Espejo de backend/app/schemas (mantener sincronizado o generar con openapi-typescript).
export type View = "anterior" | "posterior" | "lateral_derecha" | "lateral_izquierda";

export const VIEW_LABELS: Record<View, string> = {
  anterior: "Vista anterior",
  posterior: "Vista posterior",
  lateral_derecha: "Vista lateral derecha",
  lateral_izquierda: "Vista lateral izquierda",
};

export interface AssessmentConfig {
  tolerance_angle: number;
  tolerance_distance: number;
  grid_size: number;
  filter_threshold: number;
  auto_threshold: boolean;
}

export interface Point { x: number; y: number }

export interface ResultTable {
  key: string;
  title: string;
  columns: [string, string, string];
  rows: { item: string; direction: string; value: number }[];
}

export interface Calibration {
  vertex: Point; // parte superior de la cabeza
  floor: Point; // apoyo de los talones
}

export type VerticalLine = [Point, Point];

/** Punto de MediaPipe en píxeles de la imagen. */
export interface PosePoint extends Point {
  visibility: number;
}

export interface ViewResult {
  view: View;
  image_width: number | null;
  image_height: number | null;
  markers: Record<string, Point>;
  derived_points: Record<string, Point>;
  scale_ratio: number;
  grid_origin: Point;
  grid_step_px: number;
  diagnostic: Record<string, string | number | null>;
  tables: ResultTable[];
  image: string | null;
  roll_deg: number;
  threshold_used: number | null;
  estimated_points: string[];
  calibration: Calibration | null;
}

/** Modo de detección: sin marcadores (MediaPipe + estatura) o con marcadores verdes (tesis). */
export type DetectionMode = "pose" | "markers";

export interface ViewInfo {
  view: View;
  labels: Record<string, string>;
  expected_markers: number;
}

export interface MarkerCountError {
  message: string;
  expected: number;
  found: number;
  points: Point[];
  preview_image: string | null;
}

export interface Patient {
  id: number;
  name: string;
  age: number | null;
  gender: "M" | "F" | null;
  height_cm: number | null;
  weight_kg: number | null;
  occupation: string | null;
  created_at: string;
}

/** Entrada del diccionario de puntos (GET /api/points). */
export interface PointInfo {
  id: string;
  name: string;
  side: string | null;
  region: string;
  definition: string;
  location: string;
  views: View[];
  figure: "anterior" | "posterior" | "lateral";
  position: [number, number]; // en la silueta de 100 x 200
  measurements: { table: string; item: string }[];
  diagnostics: string[];
}

export interface PatientListItem extends Patient {
  evaluation_count: number;
  last_evaluation_at: string | null;
}

export type PatientInput = Omit<Patient, "id" | "created_at">;

/** Una vista lista para guardar: los puntos tal como quedaron en el editor. */
export interface ViewSubmission {
  view: View;
  landmarks: Record<string, Point>;
  scale_ratio?: number;
  calibration?: Calibration | null;
  vertical_line?: VerticalLine | null;
  estimated_points: string[];
}

export interface EvaluationCreate {
  patient_id: number;
  mode: DetectionMode;
  height_cm?: number | null;
  config: AssessmentConfig;
  notes?: string | null;
  views: ViewSubmission[];
}

export interface EvaluationSummary {
  id: number;
  patient_id: number;
  created_at: string;
  mode: DetectionMode;
  height_cm: number | null;
  views: View[];
  diagnostic: Partial<Record<View, Record<string, string | number | null>>>;
  pending_points: number;
  report_url: string;
}

export interface SavedView {
  view: View;
  image_url: string;
  overlay_url: string;
  image_width: number;
  image_height: number;
  markers: Record<string, Point>;
  derived_points: Record<string, Point>;
  calibration: Calibration | null;
  vertical_line: VerticalLine | null;
  scale_ratio: number;
  roll_deg: number;
  grid_origin: Point;
  grid_step_px: number;
  estimated_points: string[];
  diagnostic: Record<string, string | number | null>;
  tables: ResultTable[];
}

export interface Evaluation extends EvaluationSummary {
  age: number | null;
  weight_kg: number | null;
  config: AssessmentConfig;
  notes: string | null;
  patient: Patient;
  results: SavedView[];
}

export interface History {
  view: View;
  evaluations: { id: number; date: string }[];
  tables: {
    key: string;
    title: string;
    unit: string;
    rows: { item: string; values: ({ direction: string; value: number } | null)[]; change: number | null }[];
  }[];
  diagnostic: { key: string; label: string; values: (string | null)[] }[];
}
