import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { Patient, PatientInput } from "@/lib/types";

const num = (v: string) => (v.trim() === "" ? null : Number(v));

/** Datos del paciente (reemplaza patient.py, que los pedía por consola). */
export default function PatientForm({ initial, submitLabel, pending, error, onSubmit, onCancel }: {
  initial?: Patient | null;
  submitLabel: string;
  pending?: boolean;
  error?: string | null;
  onSubmit: (data: PatientInput) => void;
  onCancel?: () => void;
}) {
  const [name, setName] = useState(initial?.name ?? "");
  const [age, setAge] = useState(initial?.age?.toString() ?? "");
  const [gender, setGender] = useState<string>(initial?.gender ?? "");
  const [height, setHeight] = useState(initial?.height_cm?.toString() ?? "");
  const [weight, setWeight] = useState(initial?.weight_kg?.toString() ?? "");
  const [occupation, setOccupation] = useState(initial?.occupation ?? "");

  const submit = (e: FormEvent) => {
    e.preventDefault();
    onSubmit({
      name: name.trim() || "Anónimo",
      age: num(age),
      gender: gender === "M" || gender === "F" ? gender : null,
      height_cm: num(height),
      weight_kg: num(weight),
      occupation: occupation.trim() || null,
    });
  };

  return (
    <form onSubmit={submit} className="grid gap-4">
      <div className="grid gap-2">
        <Label htmlFor="p-nombre">Nombre</Label>
        <Input id="p-nombre" value={name} onChange={(e) => setName(e.target.value)} autoComplete="off"
          placeholder="Nombres y apellidos" autoFocus />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="grid gap-2">
          <Label htmlFor="p-edad">Edad</Label>
          <Input id="p-edad" type="number" inputMode="numeric" min={1} max={129} value={age}
            onChange={(e) => setAge(e.target.value)} className="tabular-nums" />
        </div>
        <div className="grid gap-2">
          <Label>Género</Label>
          <ToggleGroup type="single" variant="outline" value={gender} onValueChange={setGender} aria-label="Género">
            <ToggleGroupItem value="F">Femenino</ToggleGroupItem>
            <ToggleGroupItem value="M">Masculino</ToggleGroupItem>
          </ToggleGroup>
        </div>
        <div className="grid gap-2">
          <Label htmlFor="p-estatura">Estatura (cm)</Label>
          <Input id="p-estatura" type="number" inputMode="decimal" min={50} max={250} step={0.1} value={height}
            onChange={(e) => setHeight(e.target.value)} className="tabular-nums" />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="p-peso">Peso (kg)</Label>
          <Input id="p-peso" type="number" inputMode="decimal" min={1} max={499} step={0.1} value={weight}
            onChange={(e) => setWeight(e.target.value)} className="tabular-nums" />
        </div>
      </div>
      <div className="grid gap-2">
        <Label htmlFor="p-ocupacion">Ocupación</Label>
        <Input id="p-ocupacion" value={occupation} onChange={(e) => setOccupation(e.target.value)} />
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        {onCancel && <Button type="button" variant="outline" onClick={onCancel}>Cancelar</Button>}
        <Button type="submit" disabled={pending}>{pending ? "Guardando…" : submitLabel}</Button>
      </div>
    </form>
  );
}
