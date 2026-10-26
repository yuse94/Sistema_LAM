import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { useSearchParams } from "react-router";
import BodyFigure from "@/components/BodyFigure";
import PointCard, { pointTitle } from "@/components/PointCard";
import { Input } from "@/components/ui/input";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { api } from "@/lib/api";
import type { PointInfo } from "@/lib/types";
import { cn } from "@/lib/utils";

type Figure = PointInfo["figure"];
const FIGURES: { value: Figure; label: string }[] = [
  { value: "anterior", label: "Anterior" },
  { value: "posterior", label: "Posterior" },
  { value: "lateral", label: "Laterales" },
];

/** Quita tildes y mayúsculas para buscar "eias" o "trocanter" sin escribir exacto. */
const normalize = (s: string) => s.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();

/** Diccionario de puntos anatómicos: silueta navegable, buscador y ficha de cada punto. */
export default function Puntos() {
  const { data: points = [], isLoading, error } = useQuery({ queryKey: ["points"], queryFn: api.points, staleTime: Infinity });
  const [params, setParams] = useSearchParams();
  const [query, setQuery] = useState("");

  const selectedId = params.get("punto")?.toUpperCase() ?? null;
  const selected = points.find((p) => p.id === selectedId) ?? null;
  const figure: Figure = selected?.figure ?? (params.get("vista") as Figure | null) ?? "anterior";

  const select = (id: string) => setParams({ punto: id }, { replace: true });
  const setFigure = (f: Figure) => setParams({ vista: f }, { replace: true });

  const results = useMemo(() => {
    const q = normalize(query.trim());
    if (!q) return [];
    return points.filter((p) =>
      [p.id, p.name, p.side ?? "", p.region, p.definition].some((t) => normalize(t).includes(q)));
  }, [points, query]);

  const figurePoints = points.filter((p) => p.figure === figure);

  return (
    <div className="space-y-6">
      <div className="max-w-3xl space-y-1">
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Diccionario de puntos</h1>
        <p className="text-muted-foreground">
          Los 33 puntos anatómicos de la evaluación: qué son, cómo localizarlos y en qué mediciones intervienen.
          Seleccione un punto en la silueta o búsquelo por nombre.
        </p>
      </div>

      {error && <p className="text-sm text-destructive">No se pudo cargar el diccionario. Verifique que el servidor esté en ejecución.</p>}

      <div className="flex flex-wrap items-center gap-4">
        <ToggleGroup type="single" variant="outline" value={figure} aria-label="Vista"
          onValueChange={(v) => v && setFigure(v as Figure)}>
          {FIGURES.map((f) => <ToggleGroupItem key={f.value} value={f.value}>{f.label}</ToggleGroupItem>)}
        </ToggleGroup>
        <div className="relative w-full max-w-xs">
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar: EIAS, rótula, C7…"
            aria-label="Buscar punto" className="pl-9" />
        </div>
      </div>

      <div className="grid gap-8 md:grid-cols-[minmax(0,15rem)_minmax(0,1fr)] lg:grid-cols-[minmax(0,15rem)_minmax(0,16rem)_minmax(0,1fr)]">
        <div className="mx-auto w-full max-w-[15rem] md:sticky md:top-6 md:self-start">
          <BodyFigure figure={figure} points={figurePoints} selected={selectedId} onSelect={select} />
          <p className="mt-2 text-center text-xs text-muted-foreground">
            {figure === "anterior" ? "El lado derecho del paciente queda a la izquierda."
              : figure === "posterior" ? "El lado izquierdo del paciente queda a la izquierda."
                : "Lateral derecha. En la lateral izquierda los puntos son los mismos, en espejo."}
          </p>
        </div>

        <nav aria-label="Lista de puntos" className="md:col-start-2 md:row-start-1 lg:col-start-2">
          {query.trim() && (
            <p className="mb-2 text-sm text-muted-foreground" aria-live="polite">
              {results.length === 0 ? `Ningún punto coincide con "${query.trim()}".` : `${results.length} resultado${results.length === 1 ? "" : "s"}`}
            </p>
          )}
          <ul className="divide-y rounded-lg border bg-card">
            {(query.trim() ? results : figurePoints).map((p) => (
              <li key={p.id}>
                <button type="button" onClick={() => select(p.id)} aria-current={p.id === selectedId ? "true" : undefined}
                  className={cn(
                    "flex w-full items-baseline gap-3 px-3 py-2 text-left text-sm outline-none transition-colors hover:bg-muted/60 focus-visible:bg-muted",
                    p.id === selectedId && "bg-accent text-accent-foreground hover:bg-accent",
                  )}>
                  <span className="w-7 shrink-0 font-bold tabular-nums">{p.id}</span>
                  <span>{pointTitle(p)}</span>
                </button>
              </li>
            ))}
            {isLoading && <li className="px-3 py-2 text-sm text-muted-foreground">Cargando…</li>}
          </ul>
        </nav>

        <div className="md:col-span-2 lg:col-span-1">
          {selected ? (
            <PointCard point={selected} className="rounded-lg border bg-card p-5" />
          ) : (
            <p className="text-sm text-muted-foreground">Seleccione un punto para ver su ficha.</p>
          )}
          <p className="mt-4 text-xs text-muted-foreground">
            Definiciones basadas en la Tabla 2.1 de la tesis (UPS-CT008207). Las mediciones se obtienen del propio
            cálculo del sistema, por lo que siempre coinciden con las tablas de resultados.
          </p>
        </div>
      </div>
    </div>
  );
}
