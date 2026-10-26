import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";

/** Reemplaza "2. Abrir base de datos" (DB_LAM.xlsx). TODO: alta, historial de evaluaciones, exportar Excel. */
export default function Pacientes() {
  const [q, setQ] = useState("");
  const { data = [], isLoading, error } = useQuery({ queryKey: ["patients", q], queryFn: () => api.patients(q) });

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Pacientes</h1>
        <p className="text-muted-foreground">Pacientes registrados y sus datos para las evaluaciones.</p>
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
              <TableHead>Género</TableHead>
              <TableHead className="text-right">Estatura</TableHead>
              <TableHead className="pr-4">Ocupación</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((p) => (
              <TableRow key={p.id}>
                <TableCell className="pl-4 font-medium">{p.name}</TableCell>
                <TableCell className="tabular-nums">{p.age ?? "—"}</TableCell>
                <TableCell>{p.gender === "F" ? "Femenino" : p.gender === "M" ? "Masculino" : "—"}</TableCell>
                <TableCell className="text-right tabular-nums">{p.height_cm ? `${p.height_cm} cm` : "—"}</TableCell>
                <TableCell className="pr-4">{p.occupation || "—"}</TableCell>
              </TableRow>
            ))}
            {!isLoading && data.length === 0 && (
              <TableRow className="hover:bg-transparent">
                <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">
                  {error ? "No se pudo cargar la lista. Verifique que el servidor esté en ejecución."
                    : q ? `Ningún paciente coincide con "${q}".` : "Aún no hay pacientes registrados."}
                </TableCell>
              </TableRow>
            )}
            {isLoading && (
              <TableRow className="hover:bg-transparent">
                <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">Cargando pacientes…</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
