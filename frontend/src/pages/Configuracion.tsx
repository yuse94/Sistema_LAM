import { useState } from "react";
import CenterSettings from "@/components/CenterSettings";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { DEFAULT_CONFIG, loadConfig, saveConfig } from "@/lib/config";
import type { AssessmentConfig } from "@/lib/types";

// Mismos rangos que el menú "3. Cambiar configuración" de la consola.
type NumericKey = Exclude<keyof AssessmentConfig, "auto_threshold">;

const FIELDS: {
  key: NumericKey; label: string; help: string; min: number; max: number; step: number; unit: string;
}[] = [
  { key: "tolerance_angle", label: "Ángulo de tolerancia", min: 0, max: 5, step: 0.1, unit: "°",
    help: "Desviaciones angulares menores a este valor se reportan como alineadas." },
  { key: "tolerance_distance", label: "Distancia de tolerancia", min: 0, max: 3, step: 0.1, unit: " cm",
    help: "Desplazamientos menores a este valor respecto a la vertical se reportan como alineados." },
  { key: "grid_size", label: "Tamaño de la cuadrícula", min: 1, max: 10, step: 0.5, unit: " cm",
    help: "Separación entre las líneas de la cuadrícula sobre la fotografía." },
  { key: "filter_threshold", label: "Umbral del filtro verde", min: 0.2, max: 0.8, step: 0.01, unit: "",
    help: "Solo para el modo con marcadores verdes. Súbalo si aparecen puntos de más; bájelo si faltan." },
];

export default function Configuracion() {
  const [config, setConfig] = useState(loadConfig);
  const update = (next: AssessmentConfig) => { setConfig(next); saveConfig(next); };

  return (
    <div className="max-w-xl space-y-6">
      <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Configuración</h1>
      <section aria-labelledby="centro" className="space-y-3">
        <div className="space-y-1">
          <h2 id="centro" className="text-lg font-bold tracking-tight">Datos del centro</h2>
          <p className="text-muted-foreground">Aparecen en el encabezado del reporte PDF.</p>
        </div>
        <div className="rounded-lg border bg-card p-5"><CenterSettings /></div>
      </section>
      <div className="space-y-1">
        <h2 className="text-lg font-bold tracking-tight">Análisis</h2>
        <p className="text-muted-foreground">Los cambios se guardan en este navegador y se aplican a la próxima fotografía o recálculo.</p>
      </div>
      <div className="space-y-6 rounded-lg border bg-card p-5">
        {FIELDS.map((f, i) => (
          <div key={f.key} className="space-y-3">
            {i > 0 && <Separator className="mb-6" />}
            <div className="flex items-baseline justify-between gap-4">
              <Label htmlFor={f.key}>{f.label}</Label>
              <span className="text-sm font-medium tabular-nums">{config[f.key]}{f.unit}</span>
            </div>
            <Slider id={f.key} min={f.min} max={f.max} step={f.step} value={[config[f.key]]}
              onValueChange={([v]) => update({ ...config, [f.key]: v })} aria-label={f.label} />
            <p className="text-sm text-muted-foreground">{f.help}</p>
          </div>
        ))}
        <Separator />
        <div className="flex items-start justify-between gap-6">
          <div className="space-y-1">
            <Label htmlFor="auto_threshold">Umbral automático</Label>
            <p className="text-sm text-muted-foreground">
              Si con el umbral configurado no aparecen todos los marcadores, el sistema prueba otros valores. En las
              fotos de validación ningún umbral fijo sirvió para todas, porque dependen de la iluminación.
            </p>
          </div>
          <Switch id="auto_threshold" checked={config.auto_threshold}
            onCheckedChange={(v) => update({ ...config, auto_threshold: v })} />
        </div>
      </div>
      <Button variant="outline" onClick={() => update(DEFAULT_CONFIG)}>Restablecer valores</Button>
    </div>
  );
}
