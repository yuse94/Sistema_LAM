import { useRef, useState, type PointerEvent } from "react";
import type { Point } from "@/lib/types";

interface Props {
  image: string;
  width: number;
  height: number;
  markers: Record<string, Point>;
  labels: Record<string, string>;
  derived: Record<string, Point>;
  gridOrigin: Point;
  gridStep: number;
  /** Se llama al soltar un punto, con todos los puntos actualizados. */
  onChange: (markers: Record<string, Point>) => void;
}

/**
 * Imagen con la cuadrícula de referencia y los puntos anatómicos arrastrables.
 * Los puntos se guardan en coordenadas de la imagen (píxeles), igual que en la API.
 */
export default function LandmarkEditor({
  image, width, height, markers, labels, derived, gridOrigin, gridStep, onChange,
}: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [points, setPoints] = useState(markers);
  const [dragging, setDragging] = useState<string | null>(null);
  const [lastMarkers, setLastMarkers] = useState(markers);

  // Si llegan puntos nuevos del servidor (otra foto), se reemplazan los locales.
  if (markers !== lastMarkers) {
    setLastMarkers(markers);
    setPoints(markers);
  }

  const toImage = (e: PointerEvent): Point => {
    const svg = svgRef.current!;
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const p = pt.matrixTransform(svg.getScreenCTM()!.inverse());
    return { x: Math.min(Math.max(p.x, 0), width), y: Math.min(Math.max(p.y, 0), height) };
  };

  const lines = (origin: number, size: number) => {
    const out: number[] = [];
    if (gridStep <= 0) return out;
    for (let v = origin % gridStep; v <= size; v += gridStep) out.push(v);
    return out;
  };

  const r = Math.max(width, height) / 160; // radio de los puntos proporcional a la imagen

  return (
    <svg ref={svgRef} viewBox={`0 0 ${width} ${height}`} className="w-full touch-none select-none rounded bg-black"
      onPointerMove={(e) => dragging && setPoints((p) => ({ ...p, [dragging]: toImage(e) }))}
      onPointerUp={() => {
        if (dragging) onChange(points);
        setDragging(null);
      }}>
      <image href={image} width={width} height={height} />

      <g stroke="black" strokeOpacity={0.35} strokeWidth={width / 1000}>
        {lines(gridOrigin.x, width).map((x) => <line key={`v${x}`} x1={x} x2={x} y1={0} y2={height} />)}
        {lines(gridOrigin.y, height).map((y) => <line key={`h${y}`} y1={y} y2={y} x1={0} x2={width} />)}
      </g>
      <g stroke="red" strokeWidth={width / 500}>
        <line x1={gridOrigin.x} x2={gridOrigin.x} y1={0} y2={height} />
        <line y1={gridOrigin.y} y2={gridOrigin.y} x1={0} x2={width} />
      </g>

      {Object.entries(derived).map(([k, p]) => (
        <text key={k} x={p.x} y={p.y} fontSize={r * 2.5} fill="red" textAnchor="middle" dominantBaseline="middle">×</text>
      ))}

      {Object.entries(points).map(([id, p]) => (
        <g key={id} className="cursor-grab"
          onPointerDown={(e) => {
            (e.target as Element).setPointerCapture?.(e.pointerId);
            setDragging(id);
          }}>
          <title>{`${id}: ${labels[id] ?? ""}`}</title>
          <circle cx={p.x} cy={p.y} r={r * 2.2} fill="transparent" />
          <circle cx={p.x} cy={p.y} r={r} fill={dragging === id ? "#f59e0b" : "#2563eb"} stroke="white"
            strokeWidth={r / 3} />
          <text x={p.x + r * 1.6} y={p.y - r * 1.2} fontSize={r * 2.2} fill="white" stroke="black"
            strokeWidth={r / 6} paintOrder="stroke">{id}</text>
        </g>
      ))}
    </svg>
  );
}
