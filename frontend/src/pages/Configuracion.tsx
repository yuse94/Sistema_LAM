import { useState } from "react";
import { DEFAULT_CONFIG, loadConfig, saveConfig } from "@/lib/config";
import type { AssessmentConfig } from "@/lib/types";

// Mismos rangos que el menú "3. Cambiar configuración" de la consola.
const FIELDS: { key: keyof AssessmentConfig; label: string; min: number; max: number; step: number; unit: string }[] = [
  { key: "tolerance_angle", label: "Ángulo de tolerancia", min: 0, max: 5, step: 0.1, unit: "°" },
  { key: "tolerance_distance", label: "Distancia de tolerancia", min: 0, max: 3, step: 0.1, unit: "cm" },
  { key: "grid_size", label: "Tamaño de cuadrícula", min: 1, max: 10, step: 0.5, unit: "cm" },
  { key: "filter_threshold", label: "Valor umbral del filtro", min: 0.2, max: 0.8, step: 0.01, unit: "" },
];

export default function Configuracion() {
  const [config, setConfig] = useState(loadConfig);
  const update = (next: AssessmentConfig) => { setConfig(next); saveConfig(next); };

  return (
    <div className="max-w-lg space-y-6">
      <h1 className="text-2xl font-semibold">Configuración del análisis</h1>
      {FIELDS.map((f) => (
        <label key={f.key} className="block">
          <span className="flex justify-between text-sm">
            {f.label} <span className="tabular-nums">{config[f.key]} {f.unit}</span>
          </span>
          <input type="range" min={f.min} max={f.max} step={f.step} value={config[f.key]} className="w-full"
            onChange={(e) => update({ ...config, [f.key]: Number(e.target.value) })} />
        </label>
      ))}
      <button onClick={() => update(DEFAULT_CONFIG)} className="rounded border px-3 py-1.5 text-sm">
        Restablecer configuración
      </button>
    </div>
  );
}
