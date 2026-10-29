import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertCircle, ArrowLeft, RefreshCw, Ruler, Save, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import LandmarkEditor, { type EditorState } from "@/components/LandmarkEditor";
import PointCard from "@/components/PointCard";
import PointLegend from "@/components/PointLegend";
import ViewResults from "@/components/ViewResults";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Toggle } from "@/components/ui/toggle";
import { api, type EvaluateRequest } from "@/lib/api";
import { formatDateTime, VIEW_SHORT } from "@/lib/labels";
import { cn } from "@/lib/utils";
import type { Evaluation, PointInfo, View, ViewResult } from "@/lib/types";

type Shown = Pick<ViewResult, "derived_points" | "grid_origin" | "grid_step_px" | "roll_deg" | "scale_ratio" | "diagnostic" | "tables">;

interface PanelState {
  editor: EditorState;
  estimated: string[];
  result: Shown;
  edited: boolean;
}

const validHeight = (h: number) => h >= 50 && h <= 250;

/** Reabre una evaluación guardada en el editor para corregir puntos, estatura u observaciones. */
export default function EditarEvaluacion() {
  const id = Number(useParams().id);
  const { data: ev, error } = useQuery({ queryKey: ["evaluation", id], queryFn: () => api.evaluation(id) });
  if (error) return <p className="text-muted-foreground">No se encontró la evaluación.</p>;
  if (!ev) return <p className="text-muted-foreground">Cargando…</p>;
  return <Editor key={ev.id} ev={ev} />;
}

function Editor({ ev }: { ev: Evaluation }) {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { data: views = [] } = useQuery({ queryKey: ["views"], queryFn: api.views, staleTime: Infinity });
  const { data: dictionary = [] } = useQuery({ queryKey: ["points"], queryFn: api.points, staleTime: Infinity });
  const pointsById = Object.fromEntries(dictionary.map((p) => [p.id, p]));
  const labels = Object.fromEntries(views.map((v) => [v.view, v.labels])) as Partial<Record<View, Record<string, string>>>;

  const [heightCm, setHeightCm] = useState<number>(ev.height_cm ?? NaN);
  const [notes, setNotes] = useState(ev.notes ?? "");
  const [panels, setPanels] = useState<Partial<Record<View, PanelState>>>(() =>
    Object.fromEntries(ev.results.map((r) => [r.view, {
      editor: { markers: r.markers, calibration: r.calibration, verticalLine: r.vertical_line },
      estimated: r.estimated_points, result: r, edited: false,
    }])));
  const setPanel = useCallback((view: View, update: (p: PanelState) => PanelState) =>
    setPanels((prev) => ({ ...prev, [view]: update(prev[view]!) })), []);

  const pose = ev.mode === "pose";
  const heightInvalid = pose && !validHeight(heightCm);
  const pending = Object.values(panels).reduce((n, p) => n + (p?.estimated.length ?? 0), 0);

  const save = useMutation({
    mutationFn: () => api.updateEvaluation(ev.id, {
      height_cm: pose ? heightCm : null,
      notes: notes.trim() || null,
      views: ev.results.map(({ view }) => {
        const p = panels[view]!;
        return {
          view, landmarks: p.editor.markers, calibration: p.editor.calibration,
          vertical_line: p.editor.verticalLine, estimated_points: p.estimated,
        };
      }),
    }),
    onSuccess: (updated) => {
      qc.setQueryData(["evaluation", ev.id], updated);
      qc.invalidateQueries({ queryKey: ["evaluations", ev.patient_id] });
      qc.invalidateQueries({ queryKey: ["history", ev.patient_id] });
      navigate(`/evaluaciones/${ev.id}`);
    },
  });

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <Link to={`/evaluaciones/${ev.id}`}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="size-4" /> Evaluación del {formatDateTime(ev.created_at)}
        </Link>
        <div className="max-w-3xl space-y-1">
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Corregir puntos · {ev.patient.name}</h1>
          <p className="text-muted-foreground">
            Se usan la misma foto y las mismas tolerancias. Al guardar, se recalculan los resultados, la imagen y el
            reporte PDF.
          </p>
        </div>
      </div>

      <section aria-label="Datos de la evaluación"
        className="grid gap-4 rounded-lg border bg-card px-4 py-4 sm:px-5 md:grid-cols-[auto_1fr]">
        {pose && (
          <div className="space-y-2">
            <Label htmlFor="estatura">Estatura del paciente</Label>
            <div className="flex items-center gap-2">
              <Input id="estatura" type="number" inputMode="decimal" min={50} max={250} step={0.1}
                value={Number.isNaN(heightCm) ? "" : heightCm} onChange={(e) => setHeightCm(e.target.valueAsNumber)}
                aria-invalid={heightInvalid} className="w-28 tabular-nums" />
              <span className="text-sm text-muted-foreground">cm</span>
            </div>
            {heightInvalid && <p className="text-sm text-destructive">Entre 50 y 250 cm.</p>}
          </div>
        )}
        <div className="space-y-2">
          <Label htmlFor="observaciones">Observaciones</Label>
          <Textarea id="observaciones" value={notes} onChange={(e) => setNotes(e.target.value)} maxLength={4000}
            className="min-h-16" />
        </div>
      </section>

      <Tabs defaultValue={ev.results[0]?.view}>
        <TabsList variant="line" className="w-full justify-start overflow-x-auto border-b pb-1 group-data-[orientation=horizontal]/tabs:h-11">
          {ev.results.map(({ view }) => (
            <TabsTrigger key={view} value={view} className="flex-none gap-2 px-3 py-2">
              {VIEW_SHORT[view]}
              {(panels[view]?.estimated.length ?? 0) > 0 && (
                <span className="rounded-full bg-point-estimated/20 px-1.5 text-xs font-medium text-amber-800 tabular-nums">
                  {panels[view]!.estimated.length}
                </span>
              )}
            </TabsTrigger>
          ))}
        </TabsList>
        {ev.results.map((r) => (
          <TabsContent key={r.view} value={r.view} forceMount className="pt-4 data-[state=inactive]:hidden">
            <EditPanel ev={ev} view={r.view} image={r.image_url} width={r.image_width} height={r.image_height}
              state={panels[r.view]!} setPanel={setPanel} heightCm={heightCm} labels={labels[r.view] ?? {}}
              pointsById={pointsById} />
          </TabsContent>
        ))}
      </Tabs>

      <div className="flex flex-wrap items-center justify-end gap-3 border-t pt-4">
        {pending > 0 && (
          <p className="mr-auto text-sm text-amber-800">
            {pending} {pending === 1 ? "punto estimado sin revisar" : "puntos estimados sin revisar"}.
          </p>
        )}
        {save.error && <p className="text-sm text-destructive">No se pudo guardar: {save.error.message}</p>}
        <Button variant="outline" asChild><Link to={`/evaluaciones/${ev.id}`}>Cancelar</Link></Button>
        <Button onClick={() => save.mutate()} disabled={save.isPending || heightInvalid}>
          <Save /> {save.isPending ? "Guardando…" : "Guardar correcciones"}
        </Button>
      </div>
    </div>
  );
}

function EditPanel({ ev, view, image, width, height, state, setPanel, heightCm, labels, pointsById }: {
  ev: Evaluation;
  view: View;
  image: string;
  width: number;
  height: number;
  state: PanelState;
  setPanel: (view: View, update: (p: PanelState) => PanelState) => void;
  heightCm: number;
  labels: Record<string, string>;
  pointsById: Record<string, PointInfo>;
}) {
  const [selected, setSelected] = useState<string | null>(null);
  const pose = ev.mode === "pose";
  const scale = ev.results.find((r) => r.view === view)!.scale_ratio; // con marcadores, R1-R2 original

  const recalc = useMutation({
    mutationFn: (editor: EditorState) => {
      const req: EvaluateRequest = { landmarks: editor.markers, vertical_line: editor.verticalLine, config: ev.config };
      if (pose) Object.assign(req, { height_cm: heightCm, calibration: editor.calibration });
      else req.scale_ratio = scale;
      return api.evaluate(view, req);
    },
    onSuccess: (result) => setPanel(view, (p) => ({ ...p, result })),
  });

  const update = (editor: EditorState, movedId?: string) => {
    setPanel(view, (p) => ({
      ...p, editor, edited: true, estimated: movedId ? p.estimated.filter((x) => x !== movedId) : p.estimated,
    }));
    if (!pose || validHeight(heightCm)) recalc.mutate(editor);
  };

  // Con otra estatura cambia la escala: recalcular (sin marcar puntos como revisados)
  const firstHeight = useRef(heightCm);
  useEffect(() => {
    if (!pose || !validHeight(heightCm) || heightCm === firstHeight.current) return;
    const t = window.setTimeout(() => recalc.mutate(state.editor), 400);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [heightCm]);

  const setVerticalLine = (on: boolean) => {
    const line = on ? ([{ x: width * 0.06, y: height * 0.1 }, { x: width * 0.06, y: height * 0.9 }] as EditorState["verticalLine"]) : null;
    update({ ...state.editor, verticalLine: line });
  };

  const info = selected ? pointsById[selected] : undefined;
  const r = state.result;

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
      <div className="space-y-3">
        <div className="overflow-hidden rounded-xl">
          <LandmarkEditor image={image} width={width} height={height} labels={labels} state={state.editor}
            estimated={state.estimated} derived={r.derived_points} gridOrigin={r.grid_origin} gridStep={r.grid_step_px}
            rollDeg={r.roll_deg} onChange={update} selected={selected} onSelect={setSelected} />
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <PointLegend mode={ev.mode} />
          <div className="flex flex-wrap gap-2">
            {pose && (
              <Toggle variant="outline" size="sm" pressed={!!state.editor.verticalLine} onPressedChange={setVerticalLine}
                aria-label="Línea vertical de referencia">
                <Ruler /> Línea vertical
              </Toggle>
            )}
            <Button variant="outline" size="sm" onClick={() => recalc.mutate(state.editor)} disabled={recalc.isPending}>
              <RefreshCw className={cn(recalc.isPending && "animate-spin")} /> Recalcular
            </Button>
          </div>
        </div>
        {recalc.error && (
          <Alert variant="destructive">
            <AlertCircle />
            <AlertTitle>No se pudo recalcular</AlertTitle>
            <AlertDescription>{recalc.error.message}</AlertDescription>
          </Alert>
        )}
      </div>
      <section aria-label="Resultados" className="space-y-5">
        {info && (
          <div className="relative rounded-lg border bg-card p-4">
            <Button variant="ghost" size="icon-sm" className="absolute top-2 right-2" aria-label="Cerrar ficha del punto"
              onClick={() => setSelected(null)}>
              <X />
            </Button>
            <PointCard point={info} compact />
          </div>
        )}
        <ViewResults result={r} estimated={state.estimated}
          note={state.edited ? "Puntos corregidos (sin guardar)" : "Puntos guardados"} />
      </section>
    </div>
  );
}
