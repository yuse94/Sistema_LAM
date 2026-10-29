import ResultTables, { Direction } from "@/components/ResultTables";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { diagnosticLines } from "@/lib/labels";
import type { ResultTable } from "@/lib/types";

export interface ResultsData {
  scale_ratio: number;
  roll_deg: number;
  threshold_used?: number | null;
  diagnostic: Record<string, string | number | null>;
  tables: ResultTable[];
}

/** Estado de los puntos, diagnóstico y tablas de una vista. */
export default function ViewResults({ result: r, estimated, note, title = "Resultados" }: {
  result: ResultsData;
  estimated: string[];
  note?: string; // p. ej. "Puntos ajustados manualmente"
  title?: string;
}) {
  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <h3 className="text-lg font-bold tracking-tight">{title}</h3>
        <div className="flex flex-wrap gap-2 text-xs">
          {estimated.length > 0 ? (
            <Badge variant="outline" className="border-point-estimated/60 bg-point-estimated/10 text-amber-900">
              Por revisar: {estimated.join(", ")}
            </Badge>
          ) : note ? (
            <Badge variant="outline" className="text-muted-foreground">{note}</Badge>
          ) : null}
          <Badge variant="outline" className="text-muted-foreground tabular-nums">Escala {r.scale_ratio.toFixed(4)} cm/px</Badge>
          {r.threshold_used != null && (
            <Badge variant="outline" className="text-muted-foreground tabular-nums">
              Umbral del filtro {r.threshold_used.toFixed(2)}
            </Badge>
          )}
          {r.roll_deg !== 0 && (
            <Badge variant="outline" className="border-vertical-line/60 text-muted-foreground tabular-nums">
              Nivelada {r.roll_deg.toFixed(1)}°
            </Badge>
          )}
        </div>
      </div>

      <dl className="grid grid-cols-[auto_1fr] items-center gap-x-6 gap-y-2 text-sm">
        {diagnosticLines(r.diagnostic).map((d) => (
          <div key={d.key} className="contents">
            <dt className="text-muted-foreground">{d.label}</dt>
            <dd className="flex items-center gap-2">
              {d.value.length <= 9 ? <Direction value={d.value} /> : <span className="font-medium">{d.value}</span>}
              {d.angle != null && <span className="tabular-nums text-muted-foreground">{d.angle.toFixed(1)}°</span>}
            </dd>
          </div>
        ))}
      </dl>

      <Separator />
      <ResultTables tables={r.tables} />
    </div>
  );
}
