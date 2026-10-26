import { ExternalLink } from "lucide-react";
import { Link } from "react-router";
import { Badge } from "@/components/ui/badge";
import { diagnosticLabel, VIEW_SHORT } from "@/lib/labels";
import type { PointInfo } from "@/lib/types";
import { cn } from "@/lib/utils";

/** Agrupa las mediciones por tabla, conservando el orden de las tablas. */
function byTable(measurements: PointInfo["measurements"]) {
  const groups = new Map<string, string[]>();
  for (const m of measurements) groups.set(m.table, [...(groups.get(m.table) ?? []), m.item]);
  return [...groups.entries()];
}

function viewsText(p: PointInfo) {
  return p.views.length > 1 ? "vistas laterales" : `vista ${VIEW_SHORT[p.views[0]].toLowerCase()}`;
}

export function pointTitle(p: PointInfo) {
  return p.side ? `${p.name} ${p.side}` : p.name;
}

/**
 * Ficha de un punto anatómico: definición, cómo localizarlo y mediciones en las que
 * interviene. "compact" se usa dentro del editor, junto a la foto.
 */
export default function PointCard({ point, compact = false, className }: {
  point: PointInfo;
  compact?: boolean;
  className?: string;
}) {
  const tables = byTable(point.measurements);
  return (
    <article className={cn("space-y-4", className)} aria-labelledby={`punto-${point.id}`}>
      <header className="space-y-1.5">
        <div className="flex items-center gap-2">
          <Badge className="tabular-nums">{point.id}</Badge>
          <span className="text-sm text-muted-foreground">{point.region}, {viewsText(point)}</span>
        </div>
        <h2 id={`punto-${point.id}`} className={cn("font-bold tracking-tight", compact ? "text-base" : "text-xl")}>
          {pointTitle(point)}
        </h2>
      </header>

      <div className="space-y-3 text-sm leading-relaxed">
        <p>{point.definition}</p>
        <div>
          <h3 className="font-medium">Cómo localizarlo</h3>
          <p className="text-muted-foreground">{point.location}</p>
        </div>
      </div>

      <div className="space-y-2 text-sm">
        <h3 className="font-medium">Interviene en</h3>
        {tables.length === 0 && point.diagnostics.length === 0 && (
          <p className="text-muted-foreground">No interviene en ninguna medición.</p>
        )}
        <dl className="space-y-2">
          {tables.map(([table, items]) => (
            <div key={table}>
              <dt className="text-muted-foreground">{table}</dt>
              <dd className="mt-1 flex flex-wrap gap-1">
                {items.map((item) => <Badge key={item} variant="secondary">{item}</Badge>)}
              </dd>
            </div>
          ))}
          {point.diagnostics.length > 0 && (
            <div>
              <dt className="text-muted-foreground">Diagnóstico</dt>
              <dd className="mt-1 flex flex-wrap gap-1">
                {point.diagnostics.map((d) => <Badge key={d} variant="outline">{diagnosticLabel(d)}</Badge>)}
              </dd>
            </div>
          )}
        </dl>
      </div>

      {compact && (
        // Se abre en otra pestaña para no perder las fotos y los puntos de la evaluación en curso
        <Link to={`/puntos?punto=${point.id}`} target="_blank" rel="noopener"
          className="inline-flex items-center gap-1 text-sm text-primary underline-offset-4 hover:underline">
          Abrir en el diccionario de puntos <ExternalLink className="size-3.5" aria-label="(se abre en otra pestaña)" />
        </Link>
      )}
    </article>
  );
}
