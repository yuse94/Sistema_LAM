import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";

/** Reemplaza "2. Abrir base de datos" (DB_LAM.xlsx). TODO: alta, historial de evaluaciones, exportar Excel. */
export default function Pacientes() {
  const [q, setQ] = useState("");
  const { data = [], isLoading } = useQuery({ queryKey: ["patients", q], queryFn: () => api.patients(q) });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Pacientes</h1>
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar por nombre"
        className="w-full max-w-sm rounded border px-3 py-1.5" />
      {isLoading ? <p>Cargando…</p> : (
        <ul className="divide-y rounded border bg-white">
          {data.map((p) => (
            <li key={p.id} className="px-4 py-2">
              {p.name} <span className="text-sm text-slate-500">{p.age ? `${p.age} años` : ""}</span>
            </li>
          ))}
          {data.length === 0 && <li className="px-4 py-2 text-slate-500">Sin pacientes registrados</li>}
        </ul>
      )}
    </div>
  );
}
