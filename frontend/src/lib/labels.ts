import type { View } from "./types";

/** Nombres legibles de las claves del diagnóstico que devuelve la API. */
export const DIAGNOSTIC_LABELS: Record<string, string> = {
  linea_escapular_descendida: "Línea escapular descendida",
  linea_pelvica_descendida: "Línea pélvica descendida",
  cabeza_inclinada: "Cabeza inclinada",
  cabeza_inclinada_angulo: "Inclinación de la cabeza",
  cabeza_rotada: "Cabeza rotada",
  rodilla_derecha: "Rodilla derecha",
  rodilla_derecha_angulo: "Ángulo rodilla derecha",
  rodilla_izquierda: "Rodilla izquierda",
  rodilla_izquierda_angulo: "Ángulo rodilla izquierda",
  rotacion_dorsal: "Rotación dorsal",
  rotacion_pelvica: "Rotación pélvica",
  pie_izquierdo: "Pie izquierdo",
  pie_derecho: "Pie derecho",
  postura: "Postura",
  proyeccion_postural: "Proyección postural",
};

export const diagnosticLabel = (key: string) => DIAGNOSTIC_LABELS[key] ?? key.replaceAll("_", " ");

export const VIEW_SHORT: Record<View, string> = {
  anterior: "Anterior",
  posterior: "Posterior",
  lateral_derecha: "Lateral derecha",
  lateral_izquierda: "Lateral izquierda",
};
