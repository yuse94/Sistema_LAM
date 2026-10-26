import { useId, useRef, useState, type PointerEvent } from "react";
import { cn } from "@/lib/utils";
import type { Calibration, Point, VerticalLine } from "@/lib/types";

/** Todo lo que el evaluador puede mover sobre la foto. */
export interface EditorState {
  markers: Record<string, Point>;
  calibration: Calibration | null; // vértice y suelo (escala por estatura)
  verticalLine: VerticalLine | null; // referencia para nivelar
}

interface Props {
  image: string;
  width: number;
  height: number;
  labels: Record<string, string>;
  state: EditorState;
  estimated: string[]; // puntos estimados: se resaltan hasta que el evaluador los mueva
  derived: Record<string, Point>;
  gridOrigin: Point;
  gridStep: number;
  rollDeg: number;
  /** Se llama al soltar un elemento, con el estado completo y el id de lo que se movió. */
  onChange: (state: EditorState, movedId: string) => void;
  selected?: string | null; // punto anatómico resaltado (su ficha se muestra al lado)
  onSelect?: (id: string) => void;
}

const CAL_LABELS: Record<string, string> = { "cal:vertex": "Vértice", "cal:floor": "Suelo" };

function setHandle(state: EditorState, id: string, p: Point): EditorState {
  if (id === "cal:vertex" && state.calibration) return { ...state, calibration: { ...state.calibration, vertex: p } };
  if (id === "cal:floor" && state.calibration) return { ...state, calibration: { ...state.calibration, floor: p } };
  if ((id === "vline:0" || id === "vline:1") && state.verticalLine) {
    const line: VerticalLine = [...state.verticalLine];
    line[id === "vline:0" ? 0 : 1] = p;
    return { ...state, verticalLine: line };
  }
  return { ...state, markers: { ...state.markers, [id]: p } };
}

/**
 * Foto con la cuadrícula de referencia y los elementos arrastrables. Los colores salen
 * del tema (index.css) y coinciden con la leyenda: detectado, estimado, calibración y
 * línea vertical. Todo en coordenadas de la imagen (píxeles), igual que en la API.
 */
export default function LandmarkEditor({
  image, width, height, labels, state, estimated, derived, gridOrigin, gridStep, rollDeg, onChange, selected, onSelect,
}: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const clipId = useId(); // único por panel: hay varias vistas en la misma página
  const [local, setLocal] = useState(state);
  const [lastState, setLastState] = useState(state);
  const [dragging, setDragging] = useState<string | null>(null);

  // Si llega un estado nuevo desde fuera (otra foto o recálculo), reemplaza al local.
  if (state !== lastState) {
    setLastState(state);
    setLocal(state);
  }

  const toImage = (e: PointerEvent): Point => {
    const svg = svgRef.current!;
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const p = pt.matrixTransform(svg.getScreenCTM()!.inverse());
    return { x: Math.min(Math.max(p.x, 0), width), y: Math.min(Math.max(p.y, 0), height) };
  };

  const r = Math.max(width, height) / 160; // tamaño de los puntos proporcional a la imagen
  const extent = Math.hypot(width, height); // la cuadrícula rotada debe cubrir toda la foto

  const gridLines = () => {
    const lines: { key: string; x1: number; y1: number; x2: number; y2: number }[] = [];
    if (gridStep <= 0) return lines;
    const n = Math.ceil(extent / gridStep);
    for (let i = -n; i <= n; i++) {
      if (i === 0) continue;
      const d = i * gridStep;
      lines.push({ key: `v${i}`, x1: gridOrigin.x + d, y1: gridOrigin.y - extent, x2: gridOrigin.x + d, y2: gridOrigin.y + extent });
      lines.push({ key: `h${i}`, x1: gridOrigin.x - extent, y1: gridOrigin.y + d, x2: gridOrigin.x + extent, y2: gridOrigin.y + d });
    }
    return lines;
  };

  const handle = (id: string, p: Point, fillClass: string, label: string, title: string, square = false) => {
    const active = dragging === id;
    const shape = cn("stroke-white", active ? "fill-white stroke-primary" : fillClass);
    const isAnatomical = id in local.markers;
    return (
      <g key={id} className={active ? "cursor-grabbing" : "cursor-grab"}
        onPointerDown={(e) => {
          (e.target as Element).setPointerCapture?.(e.pointerId);
          setDragging(id);
          if (isAnatomical) onSelect?.(id);
        }}>
        <title>{title}</title>
        <circle cx={p.x} cy={p.y} r={r * 2.4} fill="transparent" />
        {selected === id && <circle cx={p.x} cy={p.y} r={r * 2} fill="none" stroke="white" strokeWidth={r / 2.5} />}
        {square ? (
          <rect x={p.x - r} y={p.y - r} width={r * 2} height={r * 2} className={shape} strokeWidth={r / 3} />
        ) : (
          <circle cx={p.x} cy={p.y} r={r} className={shape} strokeWidth={r / 3} />
        )}
        <text x={p.x + r * 1.7} y={p.y - r * 1.2} fontSize={r * 2.2} fontWeight={700} fill="white" stroke="black"
          strokeOpacity={0.75} strokeWidth={r / 5} paintOrder="stroke">{label}</text>
      </g>
    );
  };

  return (
    <svg ref={svgRef} viewBox={`0 0 ${width} ${height}`} role="img"
      aria-label="Fotografía con los puntos anatómicos. Arrastre un punto para corregirlo."
      className="block h-auto w-full touch-none select-none"
      onPointerMove={(e) => {
        if (dragging) setLocal((s) => setHandle(s, dragging, toImage(e)));
      }}
      onPointerUp={() => {
        if (dragging) onChange(local, dragging);
        setDragging(null);
      }}>
      <defs>
        <clipPath id={clipId}><rect width={width} height={height} /></clipPath>
      </defs>
      <image href={image} width={width} height={height} />

      {/* Cuadrícula alineada con la vertical real (rotada si hay línea de referencia) */}
      <g clipPath={`url(#${CSS.escape(clipId)})`}>
        <g transform={`rotate(${-rollDeg} ${gridOrigin.x} ${gridOrigin.y})`}>
          <g stroke="white" strokeOpacity={0.28} strokeWidth={width / 1200}>
            {gridLines().map(({ key, ...l }) => <line key={key} {...l} />)}
          </g>
          <g className="stroke-plumb" strokeWidth={width / 450}>
            <line x1={gridOrigin.x} x2={gridOrigin.x} y1={gridOrigin.y - extent} y2={gridOrigin.y + extent} />
            <line y1={gridOrigin.y} y2={gridOrigin.y} x1={gridOrigin.x - extent} x2={gridOrigin.x + extent} />
          </g>
        </g>
      </g>

      {local.verticalLine && (
        <line x1={local.verticalLine[0].x} y1={local.verticalLine[0].y} x2={local.verticalLine[1].x}
          y2={local.verticalLine[1].y} className="stroke-vertical-line" strokeWidth={r / 2}
          strokeDasharray={`${r * 2} ${r}`} />
      )}

      {Object.entries(derived).map(([k, p]) => (
        <text key={k} x={p.x} y={p.y} fontSize={r * 2.5} className="fill-plumb" textAnchor="middle"
          dominantBaseline="middle">×</text>
      ))}

      {local.verticalLine?.map((p, i) =>
        handle(`vline:${i}`, p, "fill-vertical-line", i === 0 ? "V1" : "V2",
          "Línea vertical de referencia: colóquela sobre algo vertical (puerta, esquina, plomada)", true),
      )}
      {local.calibration &&
        (["vertex", "floor"] as const).map((k) =>
          handle(`cal:${k}`, local.calibration![k], "fill-point-calibration", CAL_LABELS[`cal:${k}`],
            k === "vertex" ? "Parte superior de la cabeza" : "Apoyo de los talones en el suelo", true),
        )}
      {Object.entries(local.markers).map(([id, p]) => {
        const isEstimated = estimated.includes(id);
        return handle(id, p, isEstimated ? "fill-point-estimated" : "fill-point-detected", id,
          `${id}: ${labels[id] ?? ""}${isEstimated ? " (estimado: revisar)" : ""}`);
      })}
    </svg>
  );
}
