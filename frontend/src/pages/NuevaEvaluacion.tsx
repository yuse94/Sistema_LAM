import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import LandmarkEditor from "@/components/LandmarkEditor";
import ResultTables from "@/components/ResultTables";
import { api, isMarkerError } from "@/lib/api";
import { loadConfig } from "@/lib/config";
import { VIEW_LABELS, type Point, type View, type ViewResult } from "@/lib/types";

const VIEWS = Object.keys(VIEW_LABELS) as View[];

/**
 * Flujo que reemplaza el menú "1. Hacer análisis postural" de la consola:
 * cargar una foto por vista → revisar y ajustar los puntos → tablas recalculadas.
 * TODO fase 2: datos del paciente, guardar la evaluación y descargar el PDF.
 */
export default function NuevaEvaluacion() {
  const { data: views = [] } = useQuery({ queryKey: ["views"], queryFn: api.views, staleTime: Infinity });
  const labels = Object.fromEntries(views.map((v) => [v.view, v.labels])) as Partial<Record<View, Record<string, string>>>;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Nueva evaluación postural</h1>
        <p className="text-sm text-slate-600">
          Carga una fotografía por vista. Revisa cada punto detectado y arrástralo si no coincide con el punto anatómico;
          las tablas se recalculan al soltarlo.
        </p>
      </div>
      {VIEWS.map((view) => <ViewPanel key={view} view={view} labels={labels[view] ?? {}} />)}
    </div>
  );
}

function ViewPanel({ view, labels }: { view: View; labels: Record<string, string> }) {
  const [result, setResult] = useState<ViewResult | null>(null);
  const [edited, setEdited] = useState(false);

  const detect = useMutation({
    mutationFn: (file: File) => api.analyze(view, file, loadConfig()),
    onSuccess: (r) => { setResult(r); setEdited(false); },
  });
  const recalc = useMutation({
    mutationFn: (markers: Record<string, Point>) => api.evaluate(view, markers, result!.scale_ratio, loadConfig()),
    // La imagen no viaja en el recálculo: se conserva la de la detección.
    onSuccess: (r) => { setResult((prev) => ({ ...r, image: prev?.image ?? null, image_width: prev?.image_width ?? null, image_height: prev?.image_height ?? null })); setEdited(true); },
  });

  const err = detect.error ?? recalc.error;

  return (
    <section className="rounded-lg border bg-white p-4">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-lg font-medium">{VIEW_LABELS[view]}</h2>
        <label className="cursor-pointer rounded bg-emerald-600 px-3 py-1.5 text-sm text-white">
          {detect.isPending ? "Procesando…" : result ? "Cambiar fotografía" : "Cargar fotografía"}
          <input type="file" accept="image/*" className="hidden" disabled={detect.isPending}
            onChange={(e) => e.target.files?.[0] && detect.mutate(e.target.files[0])} />
        </label>
      </div>

      {err && (
        <div className="mt-3 rounded bg-amber-50 p-3 text-sm text-amber-900">
          {err.message}
          {isMarkerError(err) && err.body.preview_image && (
            <img src={err.body.preview_image} alt="Marcadores detectados" className="mt-2 max-h-96" />
          )}
        </div>
      )}

      {result?.image && result.image_width && result.image_height && (
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <LandmarkEditor image={result.image} width={result.image_width} height={result.image_height}
              markers={result.markers} labels={labels} derived={result.derived_points}
              gridOrigin={result.grid_origin} gridStep={result.grid_step_px}
              onChange={(m) => recalc.mutate(m)} />
            <p className="mt-1 text-xs text-slate-500">
              {recalc.isPending ? "Recalculando…" : edited ? "Puntos ajustados manualmente." : "Puntos detectados automáticamente."}
            </p>
          </div>
          <div className="space-y-4">
            <dl className="grid grid-cols-2 gap-x-4 text-sm">
              {Object.entries(result.diagnostic).map(([k, v]) => (
                <div key={k} className="contents">
                  <dt className="text-slate-500">{k.replaceAll("_", " ")}</dt>
                  <dd>{String(v)}</dd>
                </div>
              ))}
            </dl>
            <ResultTables tables={result.tables} />
          </div>
        </div>
      )}
    </section>
  );
}
