import type { AssessmentConfig } from "./types";

// Configuración del evaluador (antes configuration.json). Se guarda por navegador;
// cuando haya usuarios, pasará a guardarse en el backend.
export const DEFAULT_CONFIG: AssessmentConfig = {
  tolerance_angle: 0,
  tolerance_distance: 0,
  grid_size: 5,
  filter_threshold: 0.32,
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
