import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import ResultTables from "@/components/ResultTables";
import { api, isMarkerError } from "@/lib/api";
import { loadConfig } from "@/lib/config";
import { VIEW_LABELS, type View, type ViewResult } from "@/lib/types";

const VIEWS = Object.keys(VIEW_LABELS) as View[];

/**
 * Flujo que reemplaza el menú "1. Hacer análisis postural" de la consola:
 * cargar una foto por vista → ver tablas e imagen → (fase 2) datos del paciente y reporte.
 */
export default function NuevaEvaluacion() {
  const [results, setResults] = useState<Partial<Record<View, ViewResult>>>({});

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">Nueva evaluación postural</h1>
      {VIEWS.map((view) => (
        <ViewPanel key={view} view={view} result={results[view]}
          onResult={(r) => setResults((prev) => ({ ...prev, [view]: r }))} />
      ))}
      {/* TODO fase 2: formulario del paciente + guardar evaluación + descargar PDF */}
    </div>
  );
}

function ViewPanel({ view, result, onResult }: {
  view: View; result?: ViewResult; onResult: (r: ViewResult) => void;
}) {
  const mutation = useMutation({
    mutationFn: (file: File) => api.analyze(view, file, loadConfig()),
    onSuccess: onResult,
  });
  const err = mutation.error;

  return (
    <section className="rounded-lg border bg-white p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium">{VIEW_LABELS[view]}</h2>
        <label className="cursor-pointer rounded bg-emerald-600 px-3 py-1.5 text-sm text-white">
          {mutation.isPending ? "Procesando…" : "Cargar fotografía"}
          <input type="file" accept="image/*" className="hidden" disabled={mutation.isPending}
            onChange={(e) => e.target.files?.[0] && mutation.mutate(e.target.files[0])} />
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

      {result && (
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {result.overlay_image && <img src={result.overlay_image} alt={VIEW_LABELS[view]} className="w-full rounded" />}
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
