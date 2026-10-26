// Espejo de backend/app/schemas (mantener sincronizado o generar con openapi-typescript).
export type View = "anterior" | "posterior" | "lateral_derecha";

export const VIEW_LABELS: Record<View, string> = {
  anterior: "Vista anterior",
  posterior: "Vista posterior",
  lateral_derecha: "Vista lateral derecha",
};

export interface AssessmentConfig {
  tolerance_angle: number;
  tolerance_distance: number;
  grid_size: number;
  filter_threshold: number;
}

export interface Point { x: number; y: number }

export interface ResultTable {
  key: string;
  title: string;
  columns: [string, string, string];
  rows: { item: string; direction: string; value: number }[];
}

export interface ViewResult {
  view: View;
  image_width: number;
  image_height: number;
  markers: Record<string, Point>;
  diagnostic: Record<string, string | number | null>;
  tables: ResultTable[];
  overlay_image: string | null;
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
