import { useMutation, useQueryClient } from "@tanstack/react-query";
import PatientForm from "@/components/PatientForm";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { api } from "@/lib/api";
import type { Patient, PatientInput } from "@/lib/types";

/** Alta o edición de un paciente en un diálogo. */
export default function PatientDialog({ open, onOpenChange, patient, onSaved }: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  patient?: Patient | null; // si viene, se edita
  onSaved?: (patient: Patient) => void;
}) {
  const qc = useQueryClient();
  const save = useMutation({
    mutationFn: (data: PatientInput) => (patient ? api.updatePatient(patient.id, data) : api.createPatient(data)),
    onSuccess: (p) => {
      qc.invalidateQueries({ queryKey: ["patients"] });
      qc.setQueryData(["patient", p.id], p);
      onSaved?.(p);
      onOpenChange(false);
    },
  });

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) save.reset(); onOpenChange(o); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{patient ? "Editar paciente" : "Nuevo paciente"}</DialogTitle>
          <DialogDescription>
            La estatura se usa como escala en el modo sin marcadores; puede ajustarse en cada evaluación.
          </DialogDescription>
        </DialogHeader>
        {/* key: el formulario se reinicia con los datos actuales cada vez que se abre */}
        {open && (
          <PatientForm key={patient?.id ?? "nuevo"} initial={patient} pending={save.isPending}
            submitLabel={patient ? "Guardar cambios" : "Registrar paciente"} error={save.error?.message}
            onSubmit={(data) => save.mutate(data)} onCancel={() => onOpenChange(false)} />
        )}
      </DialogContent>
    </Dialog>
  );
}
