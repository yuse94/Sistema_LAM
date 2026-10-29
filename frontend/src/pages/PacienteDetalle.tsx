import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, FileSpreadsheet, FileText, Pencil, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import ConfirmDialog from "@/components/ConfirmDialog";
import PatientDialog from "@/components/PatientDialog";
import { patientDetails } from "@/components/PatientPicker";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { api, links } from "@/lib/api";
import { formatDate, formatDateTime, MODE_LABELS, VIEW_SHORT } from "@/lib/labels";
import { VIEW_LABELS, type EvaluationSummary, type History, type View } from "@/lib/types";

const VIEWS = Object.keys(VIEW_LABELS) as View[];

/** Ficha del paciente: datos, evaluaciones guardadas y comparación en el tiempo. */
export default function PacienteDetalle() {
  const id = Number(useParams().id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [deletingPatient, setDeletingPatient] = useState(false);
  const [deletingEval, setDeletingEval] = useState<EvaluationSummary | null>(null);

  const patient = useQuery({ queryKey: ["patient", id], queryFn: () => api.patient(id) });
  const evaluations = useQuery({ queryKey: ["evaluations", id], queryFn: () => api.evaluations(id) });
  const evals = evaluations.data ?? [];

  const removePatient = useMutation({
    mutationFn: () => api.deletePatient(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["patients"] });
      navigate("/pacientes");
    },
  });
  const removeEval = useMutation({
    mutationFn: (evalId: number) => api.deleteEvaluation(evalId),
    onSuccess: () => {
      setDeletingEval(null);
      qc.invalidateQueries({ queryKey: ["evaluations", id] });
      qc.invalidateQueries({ queryKey: ["history", id] });
      qc.invalidateQueries({ queryKey: ["patients"] });
    },
  });

  if (patient.error) {
    return (
      <div className="space-y-4">
        <BackLink />
        <p className="text-muted-foreground">No se encontró el paciente.</p>
      </div>
    );
  }
  const p = patient.data;

  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <BackLink />
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="min-w-0 space-y-1">
            <h1 className="truncate text-2xl font-bold tracking-tight sm:text-3xl">{p?.name ?? "…"}</h1>
            <p className="text-muted-foreground">{p ? patientDetails(p) || "Sin datos adicionales" : " "}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => setEditing(true)} disabled={!p}><Pencil /> Editar</Button>
            <Button variant="outline" asChild>
              <a href={links.excel(id)} download><FileSpreadsheet /> Excel</a>
            </Button>
            <Button asChild><Link to={`/?paciente=${id}`}><Plus /> Nueva evaluación</Link></Button>
          </div>
        </div>
      </div>

      <section aria-labelledby="evaluaciones" className="space-y-3">
        <h2 id="evaluaciones" className="text-lg font-bold tracking-tight">Evaluaciones</h2>
        <div className="rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="pl-4">Fecha</TableHead>
                <TableHead className="hidden md:table-cell">Detección</TableHead>
                <TableHead>Vistas</TableHead>
                <TableHead className="hidden lg:table-cell">Postura (lateral)</TableHead>
                <TableHead className="pr-4 text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {[...evals].map((e) => {
                const lateral = e.diagnostic.lateral_derecha ?? e.diagnostic.lateral_izquierda;
                return (
                  <TableRow key={e.id}>
                    <TableCell className="pl-4">
                      <Link to={`/evaluaciones/${e.id}`} className="font-medium outline-none hover:underline focus-visible:underline">
                        {formatDateTime(e.created_at)}
                      </Link>
                      {e.pending_points > 0 && (
                        <Badge variant="outline" className="ml-2 border-point-estimated/60 text-amber-900">
                          {e.pending_points} sin revisar
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="hidden text-muted-foreground md:table-cell">{MODE_LABELS[e.mode]}</TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {e.views.map((v) => <Badge key={v} variant="secondary">{VIEW_SHORT[v]}</Badge>)}
                      </div>
                    </TableCell>
                    <TableCell className="hidden lg:table-cell">{lateral ? String(lateral.postura) : "—"}</TableCell>
                    <TableCell className="pr-4">
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="icon-sm" asChild>
                          <a href={links.report(e.id)} target="_blank" rel="noreferrer" aria-label="Abrir reporte PDF"
                            title="Reporte PDF"><FileText /></a>
                        </Button>
                        <Button variant="ghost" size="icon-sm" aria-label="Eliminar evaluación" title="Eliminar"
                          onClick={() => setDeletingEval(e)}>
                          <Trash2 />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
              {!evaluations.isLoading && evals.length === 0 && (
                <TableRow className="hover:bg-transparent">
                  <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">
                    Aún no hay evaluaciones para este paciente.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </section>

      {evals.length >= 2 && <Comparison patientId={id} evaluations={evals} />}

      <section aria-labelledby="datos" className="space-y-2 border-t pt-6">
        <h2 id="datos" className="text-sm font-medium">Datos personales</h2>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Eliminar al paciente borra también sus evaluaciones y fotografías. No se puede deshacer.
        </p>
        <Button variant="outline" size="sm" className="text-destructive" onClick={() => setDeletingPatient(true)}>
          <Trash2 /> Eliminar paciente
        </Button>
      </section>

      <PatientDialog open={editing} onOpenChange={setEditing} patient={p} />
      <ConfirmDialog open={deletingPatient} onOpenChange={setDeletingPatient} title="Eliminar paciente"
        description={`Se eliminarán ${p?.name ?? "el paciente"}, sus ${evals.length} evaluaciones y todas sus fotografías.`}
        confirmLabel="Eliminar paciente" pending={removePatient.isPending} onConfirm={() => removePatient.mutate()} />
      <ConfirmDialog open={!!deletingEval} onOpenChange={(o) => !o && setDeletingEval(null)} title="Eliminar evaluación"
        description={deletingEval ? `Se eliminará la evaluación del ${formatDateTime(deletingEval.created_at)} con sus fotografías.` : ""}
        confirmLabel="Eliminar evaluación" pending={removeEval.isPending}
        onConfirm={() => deletingEval && removeEval.mutate(deletingEval.id)} />
    </div>
  );
}

function BackLink() {
  return (
    <Link to="/pacientes" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
      <ArrowLeft className="size-4" /> Pacientes
    </Link>
  );
}

const signed = (n: number, unit: string) => `${n > 0 ? "+" : n < 0 ? "−" : ""}${Math.abs(n).toFixed(1)}${unit === "°" ? "°" : ` ${unit}`}`;

/** Mediciones de una vista a lo largo de las evaluaciones, con el cambio entre la primera y la última. */
function Comparison({ patientId, evaluations }: { patientId: number; evaluations: EvaluationSummary[] }) {
  const counts = VIEWS.map((v) => [v, evaluations.filter((e) => e.views.includes(v)).length] as const);
  const available = counts.filter(([, n]) => n >= 2).map(([v]) => v);
  const [view, setView] = useState<View | null>(available[0] ?? null);
  useEffect(() => {
    if (!view || !available.includes(view)) setView(available[0] ?? null);
  }, [available, view]);

  const history = useQuery({
    queryKey: ["history", patientId, view], queryFn: () => api.history(patientId, view!), enabled: !!view,
  });

  return (
    <section aria-labelledby="comparacion" className="space-y-3">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="space-y-1">
          <h2 id="comparacion" className="text-lg font-bold tracking-tight">Comparación en el tiempo</h2>
          <p className="text-sm text-muted-foreground">
            Cambio: última evaluación menos la primera. Los valores conservan el signo de la medición.
          </p>
        </div>
        {available.length > 0 && (
          <ToggleGroup type="single" variant="outline" size="sm" value={view ?? ""}
            onValueChange={(v) => v && setView(v as View)} aria-label="Vista a comparar">
            {available.map((v) => <ToggleGroupItem key={v} value={v}>{VIEW_SHORT[v]}</ToggleGroupItem>)}
          </ToggleGroup>
        )}
      </div>
      {available.length === 0 ? (
        <p className="text-sm text-muted-foreground">Se necesitan dos evaluaciones con la misma vista para compararlas.</p>
      ) : history.data ? (
        <HistoryTable history={history.data} />
      ) : (
        <p className="text-sm text-muted-foreground">Cargando…</p>
      )}
    </section>
  );
}

function HistoryTable({ history }: { history: History }) {
  const cols = history.evaluations;
  return (
    <div className="overflow-x-auto rounded-lg border bg-card">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead className="pl-4">Medición</TableHead>
            {cols.map((e) => (
              <TableHead key={e.id} className="text-right whitespace-nowrap">
                <Link to={`/evaluaciones/${e.id}`} className="hover:underline">{formatDate(e.date)}</Link>
              </TableHead>
            ))}
            <TableHead className="pr-4 text-right">Cambio</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {history.diagnostic.map((d) => (
            <TableRow key={d.key}>
              <TableCell className="pl-4 text-muted-foreground">{d.label}</TableCell>
              {d.values.map((v, i) => <TableCell key={i} className="text-right whitespace-nowrap">{v ?? "—"}</TableCell>)}
              <TableCell className="pr-4" />
            </TableRow>
          ))}
          {history.tables.map((t) => [
            <TableRow key={t.key} className="bg-muted/50 hover:bg-muted/50">
              <TableCell colSpan={cols.length + 2} className="pl-4 text-xs font-medium tracking-wide text-muted-foreground uppercase">
                {t.title}
              </TableCell>
            </TableRow>,
            ...t.rows.map((r) => (
              <TableRow key={`${t.key}-${r.item}`}>
                <TableCell className="pl-4">{r.item}</TableCell>
                {r.values.map((v, i) => (
                  <TableCell key={i} className="text-right whitespace-nowrap tabular-nums">
                    {v ? <><span className="mr-1.5 text-xs text-muted-foreground">{v.direction}</span>{v.value.toFixed(1)}{t.unit === "°" ? "°" : ` ${t.unit}`}</> : "—"}
                  </TableCell>
                ))}
                <TableCell className="pr-4 text-right font-medium whitespace-nowrap tabular-nums">
                  {r.change == null ? "—" : signed(r.change, t.unit)}
                </TableCell>
              </TableRow>
            )),
          ])}
        </TableBody>
      </Table>
    </div>
  );
}
