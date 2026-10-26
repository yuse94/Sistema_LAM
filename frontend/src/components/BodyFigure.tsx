import { cn } from "@/lib/utils";
import type { PointInfo } from "@/lib/types";

/**
 * Silueta de referencia (lienzo 100 x 200) con los puntos de una vista. Las posiciones
 * vienen del backend (catalog.py), las mismas que usa para calcular las mediciones.
 * Anterior: el lado derecho del paciente a la izquierda. Posterior: el izquierdo a la
 * izquierda. Lateral: el paciente mira hacia la derecha.
 */
const FRONT = [
  <ellipse key="head" cx="50" cy="19" rx="9" ry="11" />,
  <rect key="neck" x="45" y="28" width="10" height="9" rx="2" />,
  <path key="torso" d="M31 37 Q50 32 69 37 L66 70 Q64 80 65 90 L35 90 Q36 80 34 70 Z" />,
  <path key="arm-l" d="M31 37 Q25 39 25 50 L24 108 Q24 113 27.5 113 Q31 113 30.5 108 L33 55 Z" />,
  <path key="arm-r" d="M69 37 Q75 39 75 50 L76 108 Q76 113 72.5 113 Q69 113 69.5 108 L67 55 Z" />,
  <path key="leg-l" d="M35 88 L50 92 L47.5 178 L40.5 178 Z" />,
  <path key="leg-r" d="M65 88 L50 92 L52.5 178 L59.5 178 Z" />,
  <path key="foot-l" d="M40 176 L48 176 L46.5 195 L36.5 195 Z" />,
  <path key="foot-r" d="M60 176 L52 176 L53.5 195 L63.5 195 Z" />,
];

const SIDE = [
  <ellipse key="head" cx="51" cy="19" rx="10" ry="11" />,
  <path key="nose" d="M60 15.5 L64.5 21 L60.5 22.5 Z" />,
  <rect key="neck" x="45" y="28" width="9" height="10" rx="2" />,
  <path key="torso" d="M44 36 Q52 34 57 37 Q63 44 62 56 Q60 66 61 76 Q63 84 61 93 L41 93 Q38 86 40 78 Q42 70 40 60 Q39 48 44 36 Z" />,
  <path key="leg" d="M42 90 L61 90 Q60 120 57 135 L56.5 183 L49 183 L48.5 135 Q44 115 42 90 Z" />,
  <path key="foot" d="M47 181 L57.5 181 Q62 186 69 192 L69 195 L44 195 Q44 188 47 181 Z" />,
  <path key="arm" d="M47.5 38 Q50 36.5 52.5 38 L53 104 Q53 109 50.5 109 Q48 109 48 104 Z" />,
];

interface Props {
  figure: PointInfo["figure"];
  points: PointInfo[]; // puntos de esta silueta
  selected?: string | null;
  onSelect?: (id: string) => void;
  className?: string;
}

export default function BodyFigure({ figure, points, selected, onSelect, className }: Props) {
  const title = figure === "anterior" ? "Vista anterior" : figure === "posterior" ? "Vista posterior" : "Vista lateral";
  return (
    <svg viewBox="0 0 100 200" className={cn("h-auto w-full", className)} role="group" aria-label={`Silueta, ${title.toLowerCase()}`}>
      <g className="fill-muted stroke-border" strokeWidth={0.8}>{figure === "lateral" ? SIDE : FRONT}</g>
      <line x1="0" x2="100" y1="195.5" y2="195.5" className="stroke-border" strokeWidth={0.6} />
      {points.map((p) => {
        const [x, y] = p.position;
        const active = p.id === selected;
        const label = `${p.id}: ${p.name}${p.side ? ` ${p.side}` : ""}`;
        return (
          <g key={p.id} role={onSelect ? "button" : undefined} tabIndex={onSelect ? 0 : undefined}
            aria-label={label} aria-pressed={onSelect ? active : undefined}
            className={cn(onSelect && "cursor-pointer outline-none focus-visible:[&>circle:last-of-type]:stroke-ring")}
            onClick={() => onSelect?.(p.id)}
            onKeyDown={(e) => {
              if (onSelect && (e.key === "Enter" || e.key === " ")) {
                e.preventDefault();
                onSelect(p.id);
              }
            }}>
            <title>{label}</title>
            <circle cx={x} cy={y} r={5} fill="transparent" />
            {active && <circle cx={x} cy={y} r={4.2} className="fill-primary/15 stroke-primary" strokeWidth={0.7} />}
            <circle cx={x} cy={y} r={active ? 2.1 : 1.6}
              className={active ? "fill-primary" : "fill-muted-foreground/70 stroke-transparent"} strokeWidth={1} />
            {active && (
              <text x={x + (x > 50 ? 6 : -6)} y={y + 1.2} fontSize={5} fontWeight={700} textAnchor={x > 50 ? "start" : "end"}
                className="fill-foreground">{p.id}</text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
