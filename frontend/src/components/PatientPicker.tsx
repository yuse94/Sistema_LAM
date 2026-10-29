import { useQuery } from "@tanstack/react-query";
import { Search, UserPlus, UserRound } from "lucide-react";
import { useState } from "react";
import PatientDialog from "@/components/PatientDialog";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { formatDate, GENDER_LABELS } from "@/lib/labels";
import type { Patient } from "@/lib/types";

export function patientDetails(p: Patient) {
  return [
    p.age ? `${p.age} años` : null,
    p.gender ? GENDER_LABELS[p.gender] : null,
    p.height_cm ? `${p.height_cm} cm` : null,
    p.occupation,
  ].filter(Boolean).join(" · ");
}

/** Paciente de la evaluación: buscar uno registrado o registrar uno nuevo. */
export default function PatientPicker({ patient, onChange }: {
  patient: Patient | null;
  onChange: (patient: Patient) => void;
}) {
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [q, setQ] = useState("");
  const { data = [], isLoading } = useQuery({
    queryKey: ["patients", q], queryFn: () => api.patients(q), enabled: open,
  });

  const pick = (p: Patient) => {
    onChange(p);
    setOpen(false);
  };

  return (
    <div className="flex min-w-0 items-center gap-3">
      <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-accent text-accent-foreground">
        <UserRound className="size-4" aria-hidden="true" />
      </div>
      <div className="min-w-0">
        {patient ? (
          <>
            <div className="truncate font-medium">{patient.name}</div>
            <div className="truncate text-sm text-muted-foreground">{patientDetails(patient) || "Sin datos adicionales"}</div>
          </>
        ) : (
          <div className="text-sm text-muted-foreground">Ningún paciente seleccionado</div>
        )}
      </div>
      <Button variant={patient ? "outline" : "default"} size="sm" onClick={() => setOpen(true)} className="ml-1">
        {patient ? "Cambiar" : "Seleccionar paciente"}
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Seleccionar paciente</DialogTitle>
            <DialogDescription>La evaluación quedará en el historial del paciente.</DialogDescription>
          </DialogHeader>
          <div className="relative">
            <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar por nombre"
              aria-label="Buscar paciente por nombre" className="pl-9" autoFocus />
          </div>
          <ul className="-mx-2 max-h-72 overflow-y-auto" aria-label="Pacientes">
            {data.map((p) => (
              <li key={p.id}>
                <button type="button" onClick={() => pick(p)}
                  className="w-full rounded-md px-2 py-2 text-left outline-none hover:bg-accent focus-visible:bg-accent focus-visible:ring-[3px] focus-visible:ring-ring/50">
                  <div className="font-medium">{p.name}</div>
                  <div className="text-sm text-muted-foreground">
                    {[patientDetails(p), p.last_evaluation_at ? `Última evaluación: ${formatDate(p.last_evaluation_at)}` : null]
                      .filter(Boolean).join(" · ") || "Sin datos adicionales"}
                  </div>
                </button>
              </li>
            ))}
            {!isLoading && data.length === 0 && (
              <li className="px-2 py-6 text-center text-sm text-muted-foreground">
                {q ? `Ningún paciente coincide con "${q}".` : "Aún no hay pacientes registrados."}
              </li>
            )}
          </ul>
          <Button variant="outline" onClick={() => setCreating(true)}>
            <UserPlus /> Registrar nuevo paciente
          </Button>
        </DialogContent>
      </Dialog>

      <PatientDialog open={creating} onOpenChange={setCreating} onSaved={pick} />
    </div>
  );
}
