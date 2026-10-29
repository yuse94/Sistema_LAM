import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertCircle, RefreshCw, Ruler, Save, Upload, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import LandmarkEditor, { STAGE_HEIGHT, type EditorState } from "@/components/LandmarkEditor";
import PatientPicker from "@/components/PatientPicker";
import PointCard from "@/components/PointCard";
import PointLegend from "@/components/PointLegend";
import ViewResults from "@/components/ViewResults";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Toggle } from "@/components/ui/toggle";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { api, isMarkerError, type EvaluateRequest } from "@/lib/api";
import { loadConfig } from "@/lib/config";
import { VIEW_SHORT } from "@/lib/labels";
import { standardizePhoto } from "@/lib/photo";
import { detectPose } from "@/lib/pose";
import { cn } from "@/lib/utils";
import {
  VIEW_LABELS, type DetectionMode, type EvaluationCreate, type Patient, type PointInfo, type View, type ViewResult,
} from "@/lib/types";

const VIEWS = Object.keys(VIEW_LABELS) as View[];

const PHOTO_HINTS: Record<View, string> = {
  anterior: "Paciente de frente, brazos relajados y pies separados a la anchura de la cadera.",
  posterior: "Paciente de espaldas, con el cabello recogido.",
  lateral_derecha: "Lado derecho hacia la cámara: el paciente mira hacia la derecha de la foto.",
  lateral_izquierda: "Lado izquierdo hacia la cámara: el paciente mira hacia la izquierda de la foto.",
};

const validHeight = (h: number) => h >= 50 && h <= 250;

const EVALUATOR_KEY = "lam.evaluador";
const readStored = (key: string) => {
  try { return localStorage.getItem(key) ?? ""; } catch { return ""; }
};
const writeStored = (key: string, value: string) => {
  try { localStorage.setItem(key, value); } catch { /* almacenamiento no disponible */ }
};

type PanelStatus = { kind: "empty" } | { kind: "review"; pending: number } | { kind: "done" };

/**
 * Evaluación postural: paciente y estatura → una foto por vista → revisar y ajustar
 * los puntos → guardar. Reemplaza el menú "1. Hacer análisis postural"; al guardar,
 * el servidor genera el overlay, el reporte PDF y la fila del Excel.
 */
export default function NuevaEvaluacion() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [params] = useSearchParams();
  const presetId = Number(params.get("paciente")) || null;
  const [patient, setPatient] = useState<Patient | null>(null);
  const [notes, setNotes] = useState("");
  const [evaluator, setEvaluator] = useState(() => readStored(EVALUATOR_KEY));
  const [consent, setConsent] = useState(false);
  const center = useQuery({ queryKey: ["center"], queryFn: api.center, staleTime: 60_000 });
  useEffect(() => {
    if (center.data?.evaluator) setEvaluator((cur) => cur || center.data.evaluator);
  }, [center.data]);
  const panels = useRef<Partial<Record<View, PanelData>>>({});
  const [loadedViews, setLoadedViews] = useState<View[]>([]);
  const { data: views = [] } = useQuery({ queryKey: ["views"], queryFn: api.views, staleTime: Infinity });
  const { data: dictionary = [] } = useQuery({ queryKey: ["points"], queryFn: api.points, staleTime: Infinity });
  const pointsById = Object.fromEntries(dictionary.map((p) => [p.id, p]));
  const labels = Object.fromEntries(views.map((v) => [v.view, v.labels])) as Partial<Record<View, Record<string, string>>>;
  const [mode, setMode] = useState<DetectionMode>("pose");
  const [heightCm, setHeightCm] = useState<number>(NaN);
  const [status, setStatus] = useState<Partial<Record<View, PanelStatus>>>({});
  const reportStatus = useCallback((view: View, s: PanelStatus) => setStatus((prev) => ({ ...prev, [view]: s })), []);
  const reportData = useCallback((view: View, d: PanelData | null) => {
    if (d) panels.current[view] = d;
    else delete panels.current[view];
    setLoadedViews(VIEWS.filter((v) => panels.current[v]));
  }, []);

  const choosePatient = useCallback((p: Patient) => {
    setPatient(p);
    if (p.height_cm) setHeightCm(p.height_cm);
  }, []);

  // /?paciente=ID (desde la ficha del paciente): se preselecciona
  const preset = useQuery({ queryKey: ["patient", presetId], queryFn: () => api.patient(presetId!), enabled: !!presetId });
  useEffect(() => {
    if (preset.data && !patient) choosePatient(preset.data);
  }, [preset.data, patient, choosePatient]);

  const heightInvalid = mode === "pose" && !Number.isNaN(heightCm) && !validHeight(heightCm);
  const pendingPoints = loadedViews.reduce((n, v) => n + (panels.current[v]?.estimated.length ?? 0), 0);
  const blocker = !patient ? "Seleccione el paciente."
    : loadedViews.length === 0 ? "Cargue al menos una fotografía."
      : mode === "pose" && !validHeight(heightCm) ? "Ingrese la estatura del paciente."
        : !consent ? "Confirme el consentimiento del paciente." : null;

  const save = useMutation({
    mutationFn: async () => {
      const views = loadedViews.map((v) => panels.current[v]!);
      const data: EvaluationCreate = {
        patient_id: patient!.id,
        mode,
        height_cm: mode === "pose" ? heightCm : null,
        config: loadConfig(),
        notes: notes.trim() || null,
        evaluator: evaluator.trim() || null,
        photo_consent: consent,
        views: views.map((d) => ({
          view: d.result.view,
          landmarks: d.editor.markers,
          calibration: d.editor.calibration,
          vertical_line: d.editor.verticalLine,
          estimated_points: d.estimated,
          ...(mode === "markers" ? { scale_ratio: d.result.scale_ratio } : {}),
        })),
      };
      // Sin marcadores se envía la foto original; con marcadores, la imagen enderezada
      // por el servidor, que es donde están las coordenadas de los puntos.
      const images = await Promise.all(views.map(async (d) => d.file ?? (await fetch(d.image)).blob()));
      return api.saveEvaluation(data, images);
    },
    onSuccess: (ev) => {
      writeStored(EVALUATOR_KEY, evaluator.trim());
      qc.invalidateQueries({ queryKey: ["patients"] });
      qc.invalidateQueries({ queryKey: ["evaluations", ev.patient_id] });
      navigate(`/evaluaciones/${ev.id}`);
    },
  });

  return (
    <div className="space-y-6">
      <div className="max-w-3xl space-y-1">
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Evaluación postural</h1>
        <p className="text-muted-foreground">
          Cargue una fotografía por vista, revise cada punto sobre la imagen y arrástrelo si no coincide con el
          punto anatómico. Las tablas se recalculan al soltarlo.{" "}
          <Link to="/guia" className="text-primary underline-offset-4 hover:underline">¿Cómo tomar las fotos?</Link>
        </p>
      </div>

      <section aria-label="Datos de la sesión"
        className="flex flex-wrap items-end gap-x-8 gap-y-4 rounded-lg border bg-card px-4 py-4 sm:px-5">
        <div className="w-full border-b pb-4">
          <PatientPicker patient={patient} onChange={choosePatient} />
        </div>
        <div className="space-y-2">
          <Label>Detección</Label>
          <ToggleGroup type="single" variant="outline" value={mode}
            onValueChange={(v) => v && setMode(v as DetectionMode)} aria-label="Modo de detección">
            <ToggleGroupItem value="pose">Sin marcadores</ToggleGroupItem>
            <ToggleGroupItem value="markers">Marcadores verdes</ToggleGroupItem>
          </ToggleGroup>
        </div>
        {mode === "pose" && (
          <div className="space-y-2">
            <Label htmlFor="estatura">Estatura del paciente</Label>
            <div className="flex items-center gap-2">
              <Input id="estatura" type="number" inputMode="decimal" min={50} max={250} step={0.1}
                value={Number.isNaN(heightCm) ? "" : heightCm} onChange={(e) => setHeightCm(e.target.valueAsNumber)}
                aria-invalid={heightInvalid} aria-describedby="estatura-ayuda" className="w-28 tabular-nums"
                placeholder="168" />
              <span className="text-sm text-muted-foreground">cm</span>
            </div>
          </div>
        )}
        <p id="estatura-ayuda" className={cn("max-w-md text-sm", heightInvalid ? "text-destructive" : "text-muted-foreground")}>
          {mode === "markers"
            ? "Requiere los marcadores verdes en el cuerpo y las referencias R1 y R2 separadas 100 cm."
            : heightInvalid
              ? "La estatura debe estar entre 50 y 250 cm."
              : "La estatura define la escala en centímetros junto con el vértice y el suelo marcados en la foto."}
        </p>
      </section>

      <Tabs defaultValue="anterior">
        <TabsList variant="line" className="w-full justify-start overflow-x-auto border-b pb-1 group-data-[orientation=horizontal]/tabs:h-11">
          {VIEWS.map((view) => (
            <TabsTrigger key={view} value={view} className="flex-none gap-2 px-3 py-2">
              {VIEW_SHORT[view]}
              <StatusMark status={status[view]} />
            </TabsTrigger>
          ))}
        </TabsList>
        {VIEWS.map((view) => (
          // forceMount: cada vista conserva su foto y sus puntos al cambiar de pestaña
          <TabsContent key={`${view}-${mode}`} value={view} forceMount className="pt-4 data-[state=inactive]:hidden">
            <ViewPanel view={view} mode={mode} heightCm={heightCm} labels={labels[view] ?? {}}
              pointsById={pointsById} onStatus={reportStatus} onData={reportData} />
          </TabsContent>
        ))}
      </Tabs>

      <section aria-label="Guardar evaluación" className="grid gap-4 rounded-lg border bg-card px-4 py-4 sm:px-5 lg:grid-cols-[1fr_auto]">
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="observaciones">Observaciones</Label>
            <Textarea id="observaciones" value={notes} onChange={(e) => setNotes(e.target.value)} maxLength={4000}
              placeholder="Motivo de consulta, hallazgos o indicaciones (aparecen en el reporte)" className="min-h-20" />
          </div>
          <div className="flex flex-wrap items-end gap-x-8 gap-y-4">
            <div className="space-y-2">
              <Label htmlFor="evaluador">Evaluador</Label>
              <Input id="evaluador" value={evaluator} onChange={(e) => setEvaluator(e.target.value)} maxLength={150}
                placeholder="Nombre del fisioterapeuta" className="w-64" />
            </div>
            <div className="flex max-w-md items-start gap-2.5 pb-1">
              <Checkbox id="consentimiento" checked={consent} onCheckedChange={(v) => setConsent(v === true)}
                className="mt-0.5" />
              <Label htmlFor="consentimiento" className="leading-snug font-normal">
                El paciente autoriza la toma y el almacenamiento de sus fotografías para esta evaluación postural.
              </Label>
            </div>
          </div>
        </div>
        <div className="flex flex-col justify-end gap-2 lg:min-w-64">
          <p className="text-sm text-muted-foreground">
            {loadedViews.length
              ? `${loadedViews.length} ${loadedViews.length === 1 ? "vista lista" : "vistas listas"}: ${loadedViews.map((v) => VIEW_SHORT[v].toLowerCase()).join(", ")}.`
              : "Ninguna vista cargada."}
            {pendingPoints > 0 && (
              <span className="block text-amber-800">
                {pendingPoints} {pendingPoints === 1 ? "punto estimado sin revisar" : "puntos estimados sin revisar"}; quedarán
                señalados en el reporte.
              </span>
            )}
          </p>
          <Button size="lg" onClick={() => save.mutate()} disabled={!!blocker || save.isPending}>
            <Save /> {save.isPending ? "Guardando…" : "Guardar evaluación"}
          </Button>
          {blocker && <p className="text-sm text-muted-foreground">{blocker}</p>}
          {save.error && <p className="text-sm text-destructive">No se pudo guardar: {save.error.message}</p>}
        </div>
      </section>
    </div>
  );
}

function StatusMark({ status }: { status?: PanelStatus }) {
  if (!status || status.kind === "empty")
    return (
      <>
        <span className="size-2 rounded-full border border-muted-foreground/50" aria-hidden="true" />
        <span className="sr-only">(sin fotografía)</span>
      </>
    );
  if (status.kind === "review")
    return (
      <span className="rounded-full bg-point-estimated/20 px-1.5 text-xs font-medium text-amber-800 tabular-nums">
        {status.pending}
        <span className="sr-only"> puntos por revisar</span>
      </span>
    );
  return (
    <>
      <span className="size-2 rounded-full bg-primary" aria-hidden="true" />
      <span className="sr-only">(revisada)</span>
    </>
  );
}

interface PanelData {
  image: string;
  file: Blob | null; // foto original (sin marcadores); con marcadores se usa la imagen enderezada
  width: number;
  height: number;
  result: ViewResult;
  editor: EditorState;
  estimated: string[];
}

function ViewPanel({ view, mode, heightCm, labels, pointsById, onStatus, onData }: {
  view: View;
  mode: DetectionMode;
  heightCm: number;
  labels: Record<string, string>;
  pointsById: Record<string, PointInfo>;
  onStatus: (view: View, status: PanelStatus) => void;
  onData: (view: View, data: PanelData | null) => void;
}) {
  const [data, setData] = useState<PanelData | null>(null);
  const [selectedPoint, setSelectedPoint] = useState<string | null>(null);
  const selectedInfo = selectedPoint ? pointsById[selectedPoint] : undefined;
  const [edited, setEdited] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    onStatus(view, !data ? { kind: "empty" } : data.estimated.length ? { kind: "review", pending: data.estimated.length } : { kind: "done" });
  }, [view, data, onStatus]);

  useEffect(() => {
    onData(view, data);
    return () => onData(view, null);
  }, [view, data, onData]);

  // Liberar la URL local de la foto al cambiarla o al salir.
  useEffect(() => () => {
    if (data?.image.startsWith("blob:")) URL.revokeObjectURL(data.image);
  }, [data?.image]);

  const detect = useMutation({
    mutationFn: async (file: File): Promise<PanelData> => {
      const config = loadConfig();
      if (mode === "markers") {
        const result = await api.analyze(view, file, config);
        return {
          image: result.image ?? "", file: null, width: result.image_width ?? 0, height: result.image_height ?? 0, result,
          editor: { markers: result.markers, calibration: null, verticalLine: null }, estimated: [],
        };
      }
      const { url, img, blob, width, height } = await standardizePhoto(file);
      try {
        const detection = await detectPose(img);
        const result = await api.pose(view, { pose: detection.pose, height_cm: heightCm, calibration: detection.calibration, config });
        return {
          image: url, file: blob, width, height, result,
          editor: { markers: result.markers, calibration: result.calibration, verticalLine: null },
          estimated: result.estimated_points,
        };
      } catch (e) {
        URL.revokeObjectURL(url);
        throw e;
      }
    },
    onSuccess: (d) => { setData(d); setEdited(false); },
  });

  const recalc = useMutation({
    mutationFn: (editor: EditorState) => {
      const req: EvaluateRequest = { landmarks: editor.markers, vertical_line: editor.verticalLine, config: loadConfig() };
      if (mode === "pose") Object.assign(req, { height_cm: heightCm, calibration: editor.calibration });
      else req.scale_ratio = data!.result.scale_ratio;
      return api.evaluate(view, req).then((result) => ({ result, editor }));
    },
    onSuccess: ({ result, editor }) => {
      setData((d) => (d ? { ...d, result, editor } : d));
      setEdited(true);
    },
  });

  const update = (editor: EditorState, movedId?: string) => {
    if (!data) return;
    if (movedId) setData({ ...data, editor, estimated: data.estimated.filter((id) => id !== movedId) });
    recalc.mutate(editor);
  };

  const setVerticalLine = (on: boolean) => {
    if (!data) return;
    const { width: w, height: h } = data;
    const line = on ? ([{ x: w * 0.06, y: h * 0.1 }, { x: w * 0.06, y: h * 0.9 }] as EditorState["verticalLine"]) : null;
    update({ ...data.editor, verticalLine: line });
  };

  const needsHeight = mode === "pose" && !validHeight(heightCm);
  const err = detect.error ?? recalc.error;
  const r = data?.result;
  const pickFile = () => fileRef.current?.click();

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
      <input ref={fileRef} type="file" accept="image/*" className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          e.target.value = ""; // permite volver a elegir la misma foto
          if (file) detect.mutate(file);
        }} />

      <div className="space-y-3">
        <div className="overflow-hidden rounded-xl bg-stage">
          {data ? (
            <LandmarkEditor image={data.image} width={data.width} height={data.height} labels={labels}
              state={data.editor} estimated={data.estimated} derived={r!.derived_points}
              gridOrigin={r!.grid_origin} gridStep={r!.grid_step_px} rollDeg={r!.roll_deg}
              onChange={(editor, movedId) => update(editor, movedId)}
              selected={selectedPoint} onSelect={setSelectedPoint} />
          ) : (
            <div className={cn("flex w-full flex-col items-center justify-center gap-4 px-6 text-center", STAGE_HEIGHT)}>
              <svg viewBox="0 0 20 32" className="h-12 w-auto text-white/25" aria-hidden="true">
                <line x1="10" y1="1" x2="10" y2="19" stroke="currentColor" strokeWidth="1.2" />
                <path d="M10 18 C6 22 5.5 25 7 27.5 C8 29.5 12 29.5 13 27.5 C14.5 25 14 22 10 18 Z" fill="currentColor" />
              </svg>
              <div className="max-w-xs space-y-1">
                <p className="font-medium text-white">{VIEW_LABELS[view]}</p>
                <p className="text-sm text-white/65">{PHOTO_HINTS[view]}</p>
              </div>
              <Button onClick={pickFile} disabled={detect.isPending || needsHeight}>
                <Upload /> {detect.isPending ? "Analizando…" : "Cargar fotografía"}
              </Button>
              {needsHeight && <p className="text-sm text-white/65">Ingrese primero la estatura del paciente.</p>}
            </div>
          )}
        </div>

        {data && (
          <div className="flex flex-wrap items-center justify-between gap-3">
            <PointLegend mode={mode} />
            <div className="flex flex-wrap gap-2">
              {mode === "pose" && (
                <Toggle variant="outline" size="sm" pressed={!!data.editor.verticalLine} onPressedChange={setVerticalLine}
                  aria-label="Línea vertical de referencia">
                  <Ruler /> Línea vertical
                </Toggle>
              )}
              <Button variant="outline" size="sm" onClick={() => update(data.editor)} disabled={recalc.isPending || needsHeight}>
                <RefreshCw className={cn(recalc.isPending && "animate-spin")} /> Recalcular
              </Button>
              <Button variant="outline" size="sm" onClick={pickFile} disabled={detect.isPending || needsHeight}>
                <Upload /> {detect.isPending ? "Analizando…" : "Cambiar fotografía"}
              </Button>
            </div>
          </div>
        )}

        {err && (
          <Alert variant="destructive">
            <AlertCircle />
            <AlertTitle>No se pudo analizar la fotografía</AlertTitle>
            <AlertDescription>
              <p>{err.message}</p>
              {isMarkerError(err) && err.body.preview_image && (
                <img src={err.body.preview_image} alt="Marcadores detectados en la fotografía" className="mt-2 max-h-80 rounded" />
              )}
            </AlertDescription>
          </Alert>
        )}
      </div>

      <section aria-label="Resultados" className="space-y-5">
        {selectedInfo && (
          <div className="relative rounded-lg border bg-card p-4">
            <Button variant="ghost" size="icon-sm" className="absolute top-2 right-2" aria-label="Cerrar ficha del punto"
              onClick={() => setSelectedPoint(null)}>
              <X />
            </Button>
            <PointCard point={selectedInfo} compact />
          </div>
        )}
        {!r ? (
          <p className="text-sm text-muted-foreground">
            Los resultados de la {VIEW_LABELS[view].toLowerCase()} aparecerán aquí al cargar la fotografía.
          </p>
        ) : (
          <ViewResults result={r} estimated={data!.estimated}
            note={edited ? "Puntos ajustados manualmente" : "Puntos detectados automáticamente"} />
        )}
      </section>
    </div>
  );
}
