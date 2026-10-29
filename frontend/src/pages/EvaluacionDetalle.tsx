import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Download, FileText, Pencil } from "lucide-react";
import { Link, useParams } from "react-router";
import { STAGE_HEIGHT } from "@/components/LandmarkEditor";
import ViewResults from "@/components/ViewResults";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api, links } from "@/lib/api";
import { formatDateTime, MODE_LABELS, VIEW_SHORT } from "@/lib/labels";
import { cn } from "@/lib/utils";
import { VIEW_LABELS, type SavedView } from "@/lib/types";

/** Evaluación guardada: imagen con los puntos, diagnóstico y tablas de cada vista. */
export default function EvaluacionDetalle() {
  const id = Number(useParams().id);
  const { data: ev, error } = useQuery({ queryKey: ["evaluation", id], queryFn: () => api.evaluation(id) });

  if (error) return <p className="text-muted-foreground">No se encontró la evaluación.</p>;
  if (!ev) return <p className="text-muted-foreground">Cargando…</p>;

  const facts = [
    MODE_LABELS[ev.mode],
    ev.evaluator ? `Evaluador: ${ev.evaluator}` : null,
    ev.height_cm ? `Estatura ${ev.height_cm} cm` : null,
    `Tolerancias ${ev.config.tolerance_angle}° · ${ev.config.tolerance_distance} cm`,
  ].filter(Boolean);

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <Link to={`/pacientes/${ev.patient_id}`}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="size-4" /> {ev.patient.name}
        </Link>
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Evaluación del {formatDateTime(ev.created_at)}</h1>
            <p className="text-muted-foreground">{facts.join(" · ")}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" asChild>
              <Link to={`/evaluaciones/${ev.id}/editar`}><Pencil /> Corregir puntos</Link>
            </Button>
            <Button variant="outline" asChild>
              <a href={links.report(ev.id, true)}><Download /> Descargar PDF</a>
            </Button>
            <Button asChild>
              <a href={links.report(ev.id)} target="_blank" rel="noreferrer"><FileText /> Ver reporte</a>
            </Button>
          </div>
        </div>
        {ev.notes && (
          <div className="max-w-3xl rounded-lg border bg-card px-4 py-3 text-sm">
            <div className="mb-1 font-medium">Observaciones</div>
            <p className="whitespace-pre-line text-muted-foreground">{ev.notes}</p>
          </div>
        )}
      </div>

      <Tabs defaultValue={ev.results[0]?.view}>
        <TabsList variant="line" className="w-full justify-start overflow-x-auto border-b pb-1 group-data-[orientation=horizontal]/tabs:h-11">
          {ev.results.map((r) => (
            <TabsTrigger key={r.view} value={r.view} className="flex-none px-3 py-2">{VIEW_SHORT[r.view]}</TabsTrigger>
          ))}
        </TabsList>
        {ev.results.map((r) => (
          <TabsContent key={r.view} value={r.view} className="pt-4">
            <SavedViewPanel result={r} />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}

function SavedViewPanel({ result: r }: { result: SavedView }) {
  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
      <div className={cn("flex items-center justify-center overflow-hidden rounded-xl bg-stage", STAGE_HEIGHT)}>
        <img src={r.overlay_url} alt={`${VIEW_LABELS[r.view]} con los puntos anatómicos y la cuadrícula`}
          width={r.image_width} height={r.image_height} className="size-full object-contain" />
      </div>
      <ViewResults result={r} estimated={r.estimated_points} />
    </div>
  );
}
