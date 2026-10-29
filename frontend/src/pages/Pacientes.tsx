import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileSpreadsheet, Search, Sparkles, UserPlus } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router";
import PatientDialog from "@/components/PatientDialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api, links } from "@/lib/api";
import { formatDate, GENDER_LABELS } from "@/lib/labels";

/** Reemplaza "2. Abrir base de datos" (DB_LAM.xlsx): pacientes, historial y exportación. */
export default function Pacientes() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [creating, setCreating] = useState(false);
  const { data = [], isLoading, error } = useQuery({ queryKey: ["patients", q], queryFn: () => api.patients(q) });
  const qc = useQueryClient();
  const demo = useMutation({
    mutationFn: api.createDemo,
    onSuccess: (p) => {
      qc.invalidateQueries({ queryKey: ["patients"] });
      navigate(`/pacientes/${p.id}`);
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Pacientes</h1>
          <p className="text-muted-foreground">Fichas de los pacientes y sus evaluaciones posturales.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {data.length > 0 && !q && !data.some((p) => p.name === "Paciente De Demostración") && (
            <Button variant="ghost" onClick={() => demo.mutate()} disabled={demo.isPending}>
              <Sparkles /> Paciente de demostración
            </Button>
          )}
          <Button variant="outline" asChild>
            <a href={links.excel()} download><FileSpreadsheet /> Exportar a Excel</a>
          </Button>
          <Button onClick={() => setCreating(true)}><UserPlus /> Nuevo paciente</Button>
        </div>
      </div>
      <div className="relative max-w-sm">
        <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar por nombre"
          aria-label="Buscar paciente por nombre" className="pl-9" />
      </div>
      <div className="rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="pl-4">Nombre</TableHead>
              <TableHead>Edad</TableHead>
              <TableHead className="hidden sm:table-cell">Género</TableHead>
              <TableHead className="hidden text-right md:table-cell">Estatura</TableHead>
              <TableHead className="text-right">Evaluaciones</TableHead>
              <TableHead className="pr-4">Última</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((p) => (
              <TableRow key={p.id} className="cursor-pointer" onClick={() => navigate(`/pacientes/${p.id}`)}>
                <TableCell className="pl-4 font-medium">
                  <Link to={`/pacientes/${p.id}`} className="outline-none hover:underline focus-visible:underline"
                    onClick={(e) => e.stopPropagation()}>
                    {p.name}
                  </Link>
                </TableCell>
                <TableCell className="tabular-nums">{p.age ?? "—"}</TableCell>
                <TableCell className="hidden sm:table-cell">{p.gender ? GENDER_LABELS[p.gender] : "—"}</TableCell>
                <TableCell className="hidden text-right tabular-nums md:table-cell">
                  {p.height_cm ? `${p.height_cm} cm` : "—"}
                </TableCell>
                <TableCell className="text-right tabular-nums">{p.evaluation_count}</TableCell>
                <TableCell className="pr-4 text-muted-foreground">
                  {p.last_evaluation_at ? formatDate(p.last_evaluation_at) : "—"}
                </TableCell>
              </TableRow>
            ))}
            {!isLoading && data.length === 0 && (
              <TableRow className="hover:bg-transparent">
                <TableCell colSpan={6} className="py-8 text-center text-muted-foreground">
                  {error ? "No se pudo cargar la lista. Verifique que el servidor esté en ejecución."
                    : q ? `Ningún paciente coincide con "${q}".` : "Aún no hay pacientes registrados."}
                  {!error && !q && (
                    <div className="mt-4 flex flex-col items-center gap-2">
                      <Button variant="outline" onClick={() => demo.mutate()} disabled={demo.isPending}>
                        <Sparkles /> {demo.isPending ? "Creando…" : "Cargar paciente de demostración"}
                      </Button>
                      <span className="text-xs">Dos evaluaciones de ejemplo con siluetas dibujadas, para conocer la app.</span>
                      {demo.error && <span className="text-xs text-destructive">{demo.error.message}</span>}
                    </div>
                  )}
                </TableCell>
              </TableRow>
            )}
            {isLoading && (
              <TableRow className="hover:bg-transparent">
                <TableCell colSpan={6} className="py-8 text-center text-muted-foreground">Cargando pacientes…</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <PatientDialog open={creating} onOpenChange={setCreating} onSaved={(p) => navigate(`/pacientes/${p.id}`)} />
    </div>
  );
}
