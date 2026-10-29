import { Check, Grid3x3, Maximize, Minus, Plus, SlidersHorizontal, Tag } from "lucide-react";
import {
  useCallback, useEffect, useId, useLayoutEffect, useRef, useState, type KeyboardEvent, type PointerEvent,
  type ReactNode,
} from "react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
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
  estimated: string[]; // puntos estimados: se resaltan hasta que el evaluador los revise
  derived: Record<string, Point>;
  gridOrigin: Point;
  gridStep: number;
  rollDeg: number;
  /** Se llama al soltar un elemento movido (o al confirmarlo), con el estado completo y su id. */
  onChange: (state: EditorState, movedId: string) => void;
  selected?: string | null; // punto anatómico resaltado (su ficha se muestra al lado)
  onSelect?: (id: string | null) => void;
}

/** Altura del visor: igual para todas las vistas y modos, sin importar la resolución de la foto. */
export const STAGE_HEIGHT = "h-[min(72vh,760px)] min-h-[380px]";

// Tamaños en píxeles de pantalla: no cambian con la resolución de la foto ni con el zoom
const HANDLE_PX = 7;
const LABEL_PX = 12;
const LOUPE_PX = 168;
const LOUPE_ZOOM = 3;
const MAX_ZOOM = 12;

const CAL_LABELS: Record<string, string> = { "cal:vertex": "Vértice", "cal:floor": "Suelo" };

type Rect = { x: number; y: number; w: number; h: number };

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

function handlePos(state: EditorState, id: string): Point | null {
  if (id === "cal:vertex") return state.calibration?.vertex ?? null;
  if (id === "cal:floor") return state.calibration?.floor ?? null;
  if (id === "vline:0" || id === "vline:1") return state.verticalLine?.[id === "vline:0" ? 0 : 1] ?? null;
  return state.markers[id] ?? null;
}

/** Vista que muestra la foto completa ocupando el visor (con el aspecto del visor). */
function fitRect(W: number, H: number, cw: number, ch: number): Rect {
  if (!cw || !ch) return { x: 0, y: 0, w: W, h: H };
  const s = Math.min(cw / W, ch / H);
  const w = cw / s, h = ch / s;
  return { x: (W - w) / 2, y: (H - h) / 2, w, h };
}

/**
 * Foto con la cuadrícula de referencia y los elementos arrastrables, con zoom, lupa y
 * ajustes de imagen para ubicar los puntos con precisión. Los colores salen del tema
 * (index.css) y coinciden con la leyenda. Las coordenadas son píxeles de la imagen,
 * igual que en la API.
 */
export default function LandmarkEditor({
  image, width, height, labels, state, estimated, derived, gridOrigin, gridStep, rollDeg, onChange, selected, onSelect,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const clipId = useId(); // único por panel: hay varias vistas en la misma página
  const [local, setLocal] = useState(state);
  const [lastState, setLastState] = useState(state);
  const [dragging, setDragging] = useState<string | null>(null);
  const [nudging, setNudging] = useState(false);
  const [size, setSize] = useState({ cw: 0, ch: 0 });
  const [view, setView] = useState<Rect | null>(null); // null = foto completa
  const [showGrid, setShowGrid] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [adjusting, setAdjusting] = useState(false);
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);

  // Si llega un estado nuevo desde fuera (otra foto o recálculo), reemplaza al local.
  if (state !== lastState) {
    setLastState(state);
    setLocal(state);
  }

  const fit = fitRect(width, height, size.cw, size.ch);
  const v = view ?? fit;
  const k = size.cw ? size.cw / v.w : 1; // píxeles de pantalla por píxel de imagen
  const zoom = fit.w / v.w;

  // Refs para los manejadores nativos (rueda) y los gestos
  const live = useRef({ v, fit, k, zoom, local, selected });
  live.current = { v, fit, k, zoom, local, selected };
  const moved = useRef(false);
  const pointers = useRef(new Map<number, Point>());
  const gesture = useRef<
    { type: "pan"; start: Point; view: Rect } | { type: "pinch"; dist: number; zoom: number; mid: Point } | null
  >(null);
  const nudgeTimer = useRef<number | undefined>(undefined);

  useLayoutEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const measure = () => setSize({ cw: el.clientWidth, ch: el.clientHeight });
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Otra foto o cambio de tamaño del visor: volver a la foto completa
  useEffect(() => setView(null), [image, width, height, size.cw, size.ch]);
  useEffect(() => () => window.clearTimeout(nudgeTimer.current), []);

  const clientToImage = useCallback((cx: number, cy: number): Point => {
    const svg = svgRef.current!;
    const pt = svg.createSVGPoint();
    pt.x = cx;
    pt.y = cy;
    const p = pt.matrixTransform(svg.getScreenCTM()!.inverse());
    return { x: p.x, y: p.y };
  }, []);

  const clampView = useCallback((r: Rect): Rect => {
    // El centro de la vista no sale de la foto
    const cx = Math.min(Math.max(r.x + r.w / 2, 0), width);
    const cy = Math.min(Math.max(r.y + r.h / 2, 0), height);
    return { ...r, x: cx - r.w / 2, y: cy - r.h / 2 };
  }, [width, height]);

  const zoomAt = useCallback((z: number, p: Point) => {
    const { v: cur, fit: f } = live.current;
    const nz = Math.min(Math.max(z, 1), MAX_ZOOM);
    if (nz <= 1.001) return setView(null);
    const w = f.w / nz, h = f.h / nz;
    setView(clampView({ x: p.x - (p.x - cur.x) * (w / cur.w), y: p.y - (p.y - cur.y) * (h / cur.h), w, h }));
  }, [clampView]);

  const zoomCenter = (z: number) => {
    const { v: cur } = live.current;
    zoomAt(z, { x: cur.x + cur.w / 2, y: cur.y + cur.h / 2 });
  };

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault(); // la rueda hace zoom sobre la foto, no desplaza la página
      zoomAt(live.current.zoom * Math.exp(-e.deltaY * 0.0015), clientToImage(e.clientX, e.clientY));
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, [zoomAt, clientToImage]);

  const clampToImage = (p: Point): Point => ({
    x: Math.min(Math.max(p.x, 0), width), y: Math.min(Math.max(p.y, 0), height),
  });

  // --- Gestos sobre el fondo: arrastrar para moverse, pellizcar para zoom -------------------
  const onBackgroundDown = (e: PointerEvent) => {
    (e.target as Element).setPointerCapture?.(e.pointerId);
    pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
    const pts = [...pointers.current.values()];
    if (pts.length === 2) {
      const mid = clientToImage((pts[0].x + pts[1].x) / 2, (pts[0].y + pts[1].y) / 2);
      gesture.current = { type: "pinch", dist: Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y), zoom, mid };
    } else if (pts.length === 1) {
      gesture.current = { type: "pan", start: { x: e.clientX, y: e.clientY }, view: v };
      onSelect?.(null);
    }
  };

  const onMove = (e: PointerEvent) => {
    if (dragging) {
      moved.current = true;
      setLocal((s) => setHandle(s, dragging, clampToImage(clientToImage(e.clientX, e.clientY))));
      return;
    }
    if (!pointers.current.has(e.pointerId)) return;
    pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
    const g = gesture.current;
    if (g?.type === "pinch" && pointers.current.size === 2) {
      const [a, b] = [...pointers.current.values()];
      zoomAt(g.zoom * (Math.hypot(a.x - b.x, a.y - b.y) / g.dist), g.mid);
    } else if (g?.type === "pan" && view) {
      const dx = (e.clientX - g.start.x) / k, dy = (e.clientY - g.start.y) / k;
      setView(clampView({ ...g.view, x: g.view.x - dx, y: g.view.y - dy }));
    }
  };

  const onUp = (e: PointerEvent) => {
    if (dragging) {
      if (moved.current) onChange(local, dragging);
      setDragging(null);
    }
    pointers.current.delete(e.pointerId);
    if (pointers.current.size === 0) gesture.current = null;
    else if (gesture.current?.type === "pinch") gesture.current = null; // queda un dedo: no se convierte en arrastre
  };

  // --- Teclado: flechas para ajuste fino del punto seleccionado -------------------------------
  const onKeyDown = (e: KeyboardEvent) => {
    if (e.key === "+" || e.key === "=") return zoomCenter(zoom * 1.5);
    if (e.key === "-") return zoomCenter(zoom / 1.5);
    if (e.key === "0") return setView(null);
    const dir = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[e.key];
    if (!dir || !selected || !(selected in local.markers)) return;
    e.preventDefault();
    const step = e.shiftKey ? 10 : 1; // píxeles de la imagen
    const p = local.markers[selected];
    const next = setHandle(local, selected, clampToImage({ x: p.x + dir[0] * step, y: p.y + dir[1] * step }));
    setLocal(next);
    setNudging(true);
    window.clearTimeout(nudgeTimer.current);
    nudgeTimer.current = window.setTimeout(() => {
      setNudging(false);
      onChange(live.current.local, selected);
    }, 600);
  };

  // --- Dibujo ------------------------------------------------------------------------------
  const r = HANDLE_PX / k;
  const extent = Math.hypot(width, height); // la cuadrícula rotada debe cubrir toda la foto
  const filter = brightness !== 100 || contrast !== 100 ? `brightness(${brightness}%) contrast(${contrast}%)` : undefined;

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
          svgRef.current?.focus({ preventScroll: true }); // para el ajuste fino con las flechas
          moved.current = false;
          setDragging(id);
          if (isAnatomical) onSelect?.(id);
        }}>
        <title>{title}</title>
        <circle cx={p.x} cy={p.y} r={r * 2.6} fill="transparent" />
        {selected === id && <circle cx={p.x} cy={p.y} r={r * 2} fill="none" stroke="white" strokeWidth={2 / k} />}
        {square ? (
          <rect x={p.x - r} y={p.y - r} width={r * 2} height={r * 2} className={shape} strokeWidth={2 / k} />
        ) : (
          <circle cx={p.x} cy={p.y} r={r} className={shape} strokeWidth={2 / k} />
        )}
        {(showLabels || selected === id || active) && (
          <text x={p.x + r * 1.6} y={p.y - r * 1.1} fontSize={LABEL_PX / k} fontWeight={700} fill="white" stroke="black"
            strokeOpacity={0.75} strokeWidth={3 / k} paintOrder="stroke">{label}</text>
        )}
      </g>
    );
  };

  const loupeId = dragging ?? (nudging ? selected ?? null : null);
  const loupeAt = loupeId ? handlePos(local, loupeId) : null;
  const selectedEstimated = !!selected && estimated.includes(selected);

  return (
    <div ref={containerRef} className={cn("relative w-full overflow-hidden bg-stage", STAGE_HEIGHT)}>
      {size.cw > 0 && (
        <svg ref={svgRef} viewBox={`${v.x} ${v.y} ${v.w} ${v.h}`} role="application" tabIndex={0}
          aria-label="Fotografía con los puntos anatómicos. Arrastre un punto para corregirlo; con un punto seleccionado, las flechas lo mueven un píxel (Mayús: diez)."
          className="block size-full touch-none outline-none select-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset"
          onPointerMove={onMove} onPointerUp={onUp} onPointerCancel={onUp} onKeyDown={onKeyDown}>
          <defs>
            <clipPath id={clipId}><rect width={width} height={height} /></clipPath>
          </defs>
          {/* Fondo: capta el arrastre para moverse y el doble clic para acercar */}
          <rect x={v.x - v.w} y={v.y - v.h} width={v.w * 3} height={v.h * 3} fill="transparent"
            className={zoom > 1 ? "cursor-move" : undefined} onPointerDown={onBackgroundDown}
            onDoubleClick={(e) => zoomAt(zoom >= MAX_ZOOM ? 1 : zoom * 2, clientToImage(e.clientX, e.clientY))} />
          <image href={image} width={width} height={height} style={{ filter }} pointerEvents="none" />

          {/* Cuadrícula alineada con la vertical real (rotada si hay línea de referencia) */}
          <g clipPath={`url(#${CSS.escape(clipId)})`} pointerEvents="none">
            <g transform={`rotate(${-rollDeg} ${gridOrigin.x} ${gridOrigin.y})`}>
              {showGrid && (
                <g stroke="white" strokeOpacity={0.3} strokeWidth={1 / k}>
                  {gridLines().map(({ key, ...l }) => <line key={key} {...l} />)}
                </g>
              )}
              <g className="stroke-plumb" strokeWidth={1.75 / k}>
                <line x1={gridOrigin.x} x2={gridOrigin.x} y1={gridOrigin.y - extent} y2={gridOrigin.y + extent} />
                <line y1={gridOrigin.y} y2={gridOrigin.y} x1={gridOrigin.x - extent} x2={gridOrigin.x + extent} />
              </g>
            </g>
          </g>

          {local.verticalLine && (
            <line x1={local.verticalLine[0].x} y1={local.verticalLine[0].y} x2={local.verticalLine[1].x}
              y2={local.verticalLine[1].y} className="stroke-vertical-line" strokeWidth={2.5 / k}
              strokeDasharray={`${12 / k} ${6 / k}`} pointerEvents="none" />
          )}

          {Object.entries(derived).map(([key, p]) => (
            <text key={key} x={p.x} y={p.y} fontSize={18 / k} className="fill-plumb" textAnchor="middle"
              dominantBaseline="middle" pointerEvents="none">×</text>
          ))}

          {local.verticalLine?.map((p, i) =>
            handle(`vline:${i}`, p, "fill-vertical-line", i === 0 ? "V1" : "V2",
              "Línea vertical de referencia: colóquela sobre algo vertical (puerta, esquina, plomada)", true),
          )}
          {local.calibration &&
            (["vertex", "floor"] as const).map((key) =>
              handle(`cal:${key}`, local.calibration![key], "fill-point-calibration", CAL_LABELS[`cal:${key}`],
                key === "vertex" ? "Parte superior de la cabeza" : "Apoyo de los talones en el suelo", true),
            )}
          {Object.entries(local.markers).map(([id, p]) => {
            const isEstimated = estimated.includes(id);
            return handle(id, p, isEstimated ? "fill-point-estimated" : "fill-point-detected", id,
              `${id}: ${labels[id] ?? ""}${isEstimated ? " (estimado: revisar)" : ""}`);
          })}
        </svg>
      )}

      {loupeAt && size.cw > 0 && (
        <Loupe image={image} width={width} height={height} filter={filter} at={loupeAt} label={loupeId!} k={k}
          markers={local.markers}
          side={(v.x + v.w / 2 > loupeAt.x) ? "right" : "left"} />
      )}

      {/* Herramientas de visualización */}
      <div className="absolute top-2 right-2 flex flex-col items-end gap-2">
        <div className="flex items-center gap-0.5 rounded-lg bg-black/60 p-1 text-white backdrop-blur-sm">
          <ToolButton label="Alejar (−)" onClick={() => zoomCenter(zoom / 1.5)} disabled={zoom <= 1}><Minus /></ToolButton>
          <span className="w-11 text-center text-xs tabular-nums" aria-live="polite">{Math.round(zoom * 100)}%</span>
          <ToolButton label="Acercar (+)" onClick={() => zoomCenter(zoom * 1.5)} disabled={zoom >= MAX_ZOOM}><Plus /></ToolButton>
          <ToolButton label="Ver la foto completa (0)" onClick={() => setView(null)} disabled={zoom <= 1}><Maximize /></ToolButton>
          <span className="mx-0.5 h-5 w-px bg-white/25" aria-hidden="true" />
          <ToolButton label="Cuadrícula" pressed={showGrid} onClick={() => setShowGrid((s) => !s)}><Grid3x3 /></ToolButton>
          <ToolButton label="Nombres de los puntos" pressed={showLabels} onClick={() => setShowLabels((s) => !s)}><Tag /></ToolButton>
          <ToolButton label="Brillo y contraste" pressed={adjusting || !!filter} onClick={() => setAdjusting((s) => !s)}>
            <SlidersHorizontal />
          </ToolButton>
        </div>
        {adjusting && (
          <div className="w-56 space-y-3 rounded-lg border bg-card p-3 text-card-foreground shadow-lg">
            <AdjustSlider label="Brillo" value={brightness} onChange={setBrightness} />
            <AdjustSlider label="Contraste" value={contrast} onChange={setContrast} />
            <Button variant="outline" size="xs" className="w-full" disabled={!filter}
              onClick={() => { setBrightness(100); setContrast(100); }}>
              Restablecer
            </Button>
          </div>
        )}
      </div>

      {/* Punto seleccionado */}
      {selected && selected in local.markers && (
        <div className="absolute bottom-2 left-2 flex max-w-[calc(100%-1rem)] flex-wrap items-center gap-2 rounded-lg bg-black/60 px-2.5 py-1.5 text-xs text-white backdrop-blur-sm">
          <span><span className="font-bold">{selected}</span> · {labels[selected] ?? ""}</span>
          {selectedEstimated && (
            <Button size="xs" variant="secondary" onClick={() => onChange(local, selected)}>
              <Check /> Confirmar ubicación
            </Button>
          )}
          <span className="hidden text-white/70 sm:inline">Flechas: ajuste fino · Mayús: ×10</span>
        </div>
      )}
      {!selected && (
        <p className="pointer-events-none absolute bottom-2 left-2 hidden rounded-lg bg-black/50 px-2.5 py-1.5 text-xs text-white/80 md:block">
          Rueda o pellizco: zoom · Arrastre el fondo para moverse · Doble clic: acercar
        </p>
      )}
    </div>
  );
}

function ToolButton({ label, pressed, onClick, disabled, children }: {
  label: string; pressed?: boolean; onClick: () => void; disabled?: boolean; children: ReactNode;
}) {
  return (
    <button type="button" aria-label={label} title={label} aria-pressed={pressed} onClick={onClick} disabled={disabled}
      className={cn(
        "inline-flex size-8 items-center justify-center rounded-md transition-colors outline-none hover:bg-white/15 focus-visible:ring-2 focus-visible:ring-white/70 disabled:opacity-40 [&_svg]:size-4",
        pressed && "bg-white/20",
      )}>
      {children}
    </button>
  );
}

function AdjustSlider({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-xs">
        <span>{label}</span>
        <span className="tabular-nums text-muted-foreground">{value}%</span>
      </div>
      <Slider value={[value]} min={40} max={220} step={5} onValueChange={([x]) => onChange(x)} aria-label={label} />
    </div>
  );
}

/** Lupa con mira: muestra ampliada la zona del punto que se está moviendo. */
function Loupe({ image, width, height, filter, at, label, k, markers, side }: {
  image: string; width: number; height: number; filter?: string; at: Point; label: string; k: number;
  markers: Record<string, Point>; side: "left" | "right";
}) {
  const kk = Math.max(k * LOUPE_ZOOM, 1.5); // píxeles de pantalla por píxel de imagen dentro de la lupa
  const span = LOUPE_PX / kk;
  const x0 = at.x - span / 2, y0 = at.y - span / 2;
  return (
    <div aria-hidden="true"
      className={cn("pointer-events-none absolute top-2 overflow-hidden rounded-full border-2 border-white bg-stage shadow-xl",
        side === "left" ? "left-2" : "right-2 top-14")}
      style={{ width: LOUPE_PX, height: LOUPE_PX }}>
      <svg viewBox={`${x0} ${y0} ${span} ${span}`} className="size-full">
        <image href={image} width={width} height={height} style={{ filter }} />
        {Object.entries(markers).filter(([id]) => id !== label).map(([id, p]) => (
          <circle key={id} cx={p.x} cy={p.y} r={3 / kk} className="fill-point-detected" stroke="white" strokeWidth={1 / kk} />
        ))}
        <g strokeWidth={3 / kk} stroke="black" strokeOpacity={0.6}>
          <line x1={x0} x2={x0 + span} y1={at.y} y2={at.y} />
          <line y1={y0} y2={y0 + span} x1={at.x} x2={at.x} />
        </g>
        <g strokeWidth={1.2 / kk} stroke="white">
          <line x1={x0} x2={at.x - 6 / kk} y1={at.y} y2={at.y} />
          <line x1={at.x + 6 / kk} x2={x0 + span} y1={at.y} y2={at.y} />
          <line y1={y0} y2={at.y - 6 / kk} x1={at.x} x2={at.x} />
          <line y1={at.y + 6 / kk} y2={y0 + span} x1={at.x} x2={at.x} />
        </g>
        <circle cx={at.x} cy={at.y} r={6 / kk} fill="none" className="stroke-primary" strokeWidth={1.5 / kk} />
      </svg>
      <span className="absolute bottom-3 left-1/2 -translate-x-1/2 rounded bg-black/60 px-1.5 text-[11px] font-bold text-white">
        {label.startsWith("cal:") ? CAL_LABELS[label] : label.startsWith("vline:") ? "Línea" : label} · ×{(kk / k).toFixed(1)}
      </span>
    </div>
  );
}
