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

export const MODE_LABELS = {
  pose: "Sin marcadores",
  markers: "Marcadores verdes",
} as const;

const dateFmt = new Intl.DateTimeFormat("es-EC", { day: "numeric", month: "short", year: "numeric" });
const dateTimeFmt = new Intl.DateTimeFormat("es-EC", {
  day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
});

/** Fechas de la API (UTC con zona) en hora local. */
export const formatDate = (iso: string) => dateFmt.format(new Date(iso));
export const formatDateTime = (iso: string) => dateTimeFmt.format(new Date(iso));

export const GENDER_LABELS: Record<string, string> = { M: "Masculino", F: "Femenino" };

/** Diagnóstico como texto: une la clasificación con su ángulo ("Valgo (3.2°)"). */
export function diagnosticLines(diagnostic: Record<string, string | number | null>) {
  return Object.entries(diagnostic)
    .filter(([k]) => !(k.endsWith("_angulo") && k.slice(0, -7) in diagnostic))
    .map(([k, v]) => {
      const angle = diagnostic[`${k}_angulo`];
      const text = v == null ? "—" : String(v);
      return {
        key: k,
        label: diagnosticLabel(k),
        value: text,
        angle: typeof angle === "number" && v !== "N/A" ? angle : null,
      };
    });
}
