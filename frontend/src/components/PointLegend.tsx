import { cn } from "@/lib/utils";

const ITEMS = [
  { key: "detected", label: "Detectado", swatch: "rounded-full bg-point-detected", modes: ["pose", "markers"] },
  { key: "estimated", label: "Estimado: revisar", swatch: "rounded-full bg-point-estimated", modes: ["pose"] },
  { key: "calibration", label: "Vértice y suelo", swatch: "rounded-[2px] bg-point-calibration", modes: ["pose"] },
  { key: "vertical", label: "Línea vertical", swatch: "rounded-[2px] bg-vertical-line", modes: ["pose"] },
  { key: "plumb", label: "Referencia", swatch: "h-0.5 w-3 bg-plumb", modes: ["pose", "markers"] },
] as const;

/** Qué significa cada color del editor. Mismos tokens que los puntos. */
export default function PointLegend({ mode }: { mode: "pose" | "markers" }) {
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
      {ITEMS.filter((i) => (i.modes as readonly string[]).includes(mode)).map((i) => (
        <li key={i.key} className="flex items-center gap-1.5">
          <span className={cn("inline-block size-2.5", i.swatch)} aria-hidden="true" />
          {i.label}
        </li>
      ))}
    </ul>
  );
}
