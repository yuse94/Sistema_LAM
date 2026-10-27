import type { AssessmentConfig } from "./types";

// Configuración del evaluador (antes configuration.json). Se guarda por navegador;
// cuando haya usuarios, pasará a guardarse en el backend.
export const DEFAULT_CONFIG: AssessmentConfig = {
  // Validado con las ilustraciones de tipos de postura (docs/VALIDACION.md)
  tolerance_angle: 1,
  tolerance_distance: 0.5,
  grid_size: 5,
  filter_threshold: 0.32,
  auto_threshold: true,
};

const KEY = "lam.config";

export function loadConfig(): AssessmentConfig {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? { ...DEFAULT_CONFIG, ...JSON.parse(raw) } : DEFAULT_CONFIG;
  } catch {
    return DEFAULT_CONFIG;
  }
}

export function saveConfig(config: AssessmentConfig) {
  try {
    localStorage.setItem(KEY, JSON.stringify(config));
  } catch {
    /* almacenamiento no disponible */
  }
}
