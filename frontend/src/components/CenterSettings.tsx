import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ImageUp, Trash2 } from "lucide-react";
import { useRef, useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import type { Center } from "@/lib/types";

/** Nombre, contacto, evaluador y logo del centro: aparecen en el reporte PDF. */
export default function CenterSettings() {
  const { data } = useQuery({ queryKey: ["center"], queryFn: api.center });
  if (!data) return <p className="text-sm text-muted-foreground">Cargando…</p>;
  return <CenterForm key={data.logo_url ?? "sin-logo"} center={data} />;
}

function CenterForm({ center }: { center: Center }) {
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [name, setName] = useState(center.name);
  const [contact, setContact] = useState(center.contact);
  const [evaluator, setEvaluator] = useState(center.evaluator);
  const [logoVersion, setLogoVersion] = useState(0); // fuerza recargar la vista previa

  const refresh = () => qc.invalidateQueries({ queryKey: ["center"] });
  const save = useMutation({ mutationFn: () => api.updateCenter({ name, contact, evaluator }), onSuccess: refresh });
  const upload = useMutation({
    mutationFn: (file: File) => api.uploadLogo(file),
    onSuccess: () => { setLogoVersion((v) => v + 1); refresh(); },
  });
  const removeLogo = useMutation({ mutationFn: api.deleteLogo, onSuccess: refresh });
  const dirty = name !== center.name || contact !== center.contact || evaluator !== center.evaluator;

  const submit = (e: FormEvent) => {
    e.preventDefault();
    save.mutate();
  };

  return (
    <form onSubmit={submit} className="space-y-5">
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex h-20 w-44 items-center justify-center overflow-hidden rounded-md border bg-background">
          {center.logo_url ? (
            <img src={`${center.logo_url}?v=${logoVersion}`} alt="Logo del centro" className="max-h-full max-w-full object-contain p-1" />
          ) : (
            <span className="text-xs text-muted-foreground">Sin logo</span>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          <input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp" className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              e.target.value = "";
              if (f) upload.mutate(f);
            }} />
          <Button type="button" variant="outline" size="sm" onClick={() => fileRef.current?.click()} disabled={upload.isPending}>
            <ImageUp /> {upload.isPending ? "Subiendo…" : center.logo_url ? "Cambiar logo" : "Subir logo"}
          </Button>
          {center.logo_url && (
            <Button type="button" variant="ghost" size="sm" onClick={() => removeLogo.mutate()} disabled={removeLogo.isPending}>
              <Trash2 /> Quitar
            </Button>
          )}
        </div>
        {upload.error && <p className="w-full text-sm text-destructive">{upload.error.message}</p>}
      </div>
      <div className="grid gap-2">
        <Label htmlFor="centro-nombre">Nombre del centro</Label>
        <Input id="centro-nombre" value={name} onChange={(e) => setName(e.target.value)} maxLength={150}
          placeholder="Centro de Rehabilitación…" />
      </div>
      <div className="grid gap-2">
        <Label htmlFor="centro-contacto">Contacto</Label>
        <Input id="centro-contacto" value={contact} onChange={(e) => setContact(e.target.value)} maxLength={250}
          placeholder="Dirección · teléfono · correo" />
      </div>
      <div className="grid gap-2">
        <Label htmlFor="centro-evaluador">Evaluador por defecto</Label>
        <Input id="centro-evaluador" value={evaluator} onChange={(e) => setEvaluator(e.target.value)} maxLength={150}
          placeholder="Nombre del fisioterapeuta" />
        <p className="text-sm text-muted-foreground">Se propone al iniciar cada evaluación; puede cambiarse en ella.</p>
      </div>
      <div className="flex items-center gap-3">
        <Button type="submit" disabled={!dirty || save.isPending}>{save.isPending ? "Guardando…" : "Guardar datos"}</Button>
        {save.isSuccess && !dirty && <span className="text-sm text-muted-foreground">Guardado.</span>}
        {save.error && <span className="text-sm text-destructive">{save.error.message}</span>}
      </div>
    </form>
  );
}
