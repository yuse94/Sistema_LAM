import { Camera, CheckCircle2, Lightbulb, Ruler, Shirt, TriangleAlert } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router";
import { Button } from "@/components/ui/button";

const VIEWS = [
  { title: "Anterior", text: "De frente a la cámara, mirada al horizonte, brazos relajados a los lados y pies separados al ancho de la cadera." },
  { title: "Posterior", text: "De espaldas a la cámara, misma posición de pies. Cabello recogido para que se vean el cuello y los hombros." },
  { title: "Lateral derecha", text: "Lado derecho hacia la cámara: el paciente mira hacia la derecha de la foto. Brazos relajados, sin tapar la cadera." },
  { title: "Lateral izquierda", text: "Lado izquierdo hacia la cámara: el paciente mira hacia la izquierda de la foto." },
];

/** Protocolo de toma de fotografías: de su calidad depende la de los resultados. */
export default function GuiaCaptura() {
  return (
    <div className="max-w-4xl space-y-8">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Guía de captura</h1>
        <p className="text-muted-foreground">
          Cómo tomar las fotografías. Una foto bien tomada ahorra correcciones y da resultados comparables entre
          evaluaciones.
        </p>
      </div>

      <SetupDiagram />

      <div className="grid gap-4 md:grid-cols-2">
        <Card icon={<Camera />} title="Cámara">
          <li>Celular o cámara <b>en trípode</b>, en posición vertical, sin zoom digital.</li>
          <li>A la <b>altura de la cadera</b> del paciente (unos 90–100 cm del suelo) y nivelada.</li>
          <li>A <b>2,5–3 m</b> del paciente: el cuerpo entero debe entrar con margen sobre la cabeza y bajo los pies.</li>
          <li>Misma distancia y altura en todas las vistas y en los controles.</li>
        </Card>
        <Card icon={<Lightbulb />} title="Espacio">
          <li>Fondo liso y claro, sin objetos detrás del paciente.</li>
          <li>Luz pareja de frente o desde el techo; evite contraluz y sombras marcadas.</li>
          <li>Suelo plano. Marque en el piso dónde se para el paciente para repetir la posición.</li>
        </Card>
        <Card icon={<Shirt />} title="Paciente">
          <li>Ropa ajustada o deportiva corta (short, top) que deje ver hombros, cadera y rodillas.</li>
          <li>Descalzo, cabello recogido, sin accesorios que tapen los puntos.</li>
          <li>Postura habitual y relajada: no corregirse ni «pararse derecho» para la foto.</li>
          <li>Pida autorización para fotografiarlo; la app la registra al guardar.</li>
        </Card>
        <Card icon={<Ruler />} title="Referencias">
          <li>
            <b>Sin marcadores:</b> mida la <b>estatura</b> del paciente (es la escala). Deje visible algo vertical,
            como el marco de una puerta o una plomada, para usar la herramienta «Línea vertical».
          </li>
          <li>
            <b>Con marcadores verdes:</b> coloque las referencias R1 y R2 separadas exactamente 100 cm y <b>en el mismo
            plano que el paciente</b> (no en la pared del fondo): si quedan más lejos, la escala se exagera.
          </li>
        </Card>
      </div>

      <section aria-labelledby="vistas" className="space-y-3">
        <h2 id="vistas" className="text-lg font-bold tracking-tight">Las cuatro vistas</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          {VIEWS.map((v) => (
            <div key={v.title} className="rounded-lg border bg-card p-4">
              <div className="mb-1 font-medium">{v.title}</div>
              <p className="text-sm text-muted-foreground">{v.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section aria-labelledby="revisar" className="space-y-3 rounded-lg border bg-card p-5">
        <h2 id="revisar" className="flex items-center gap-2 text-lg font-bold tracking-tight">
          <TriangleAlert className="size-5 text-point-estimated" aria-hidden="true" /> Al revisar los puntos
        </h2>
        <ul className="space-y-2 text-sm">
          <li>Los puntos <b className="text-amber-700">ámbar</b> son estimados: ubíquelos sobre la referencia anatómica (EIAS, EIPS, C7, T5…).
            Toque un punto para ver su definición.</li>
          <li>Use el zoom (rueda o pellizco), la lupa que aparece al arrastrar y las flechas del teclado para el ajuste fino.</li>
          <li>En el modo sin marcadores, coloque «Vértice» en lo alto de la cabeza y «Suelo» en el apoyo de los talones.</li>
          <li>Los ángulos de la pelvis en la vista lateral dependen mucho de EIAS y EIPS: revíselos siempre.</li>
        </ul>
      </section>

      <Button asChild><Link to="/">Ir a la evaluación</Link></Button>
    </div>
  );
}

function Card({ icon, title, children }: { icon: ReactNode; title: string; children: ReactNode }) {
  return (
    <section className="rounded-lg border bg-card p-5">
      <h2 className="mb-3 flex items-center gap-2 font-bold tracking-tight [&_svg]:size-5 [&_svg]:text-primary">
        {icon} {title}
      </h2>
      <ul className="space-y-2 text-sm [&_li]:flex [&_li]:gap-2 [&_li]:before:mt-1.5 [&_li]:before:size-1.5 [&_li]:before:shrink-0 [&_li]:before:rounded-full [&_li]:before:bg-primary/60 [&_li]:before:content-['']">
        {children}
      </ul>
    </section>
  );
}

/** Esquema lateral de la toma: cámara en trípode a la altura de la cadera, a 2,5–3 m. */
function SetupDiagram() {
  return (
    <figure className="rounded-lg border bg-card p-4">
      <svg viewBox="0 0 640 230" className="h-auto w-full" role="img"
        aria-label="Esquema: cámara en trípode a unos 95 cm de altura y a 2,5 a 3 metros del paciente, de pie frente a un fondo liso.">
        <rect x="0" y="0" width="640" height="230" className="fill-background" />
        <line x1="20" y1="200" x2="620" y2="200" className="stroke-border" strokeWidth="3" />
        {/* Fondo */}
        <rect x="585" y="20" width="12" height="180" className="fill-muted" />
        {/* Paciente */}
        <g className="fill-muted-foreground/70">
          <circle cx="520" cy="44" r="14" />
          <rect x="508" y="60" width="24" height="62" rx="9" />
          <rect x="510" y="118" width="9" height="80" rx="4" />
          <rect x="521" y="118" width="9" height="80" rx="4" />
        </g>
        {/* Cámara y trípode */}
        <g className="stroke-primary" strokeWidth="3" fill="none">
          <line x1="90" y1="122" x2="70" y2="200" />
          <line x1="90" y1="122" x2="110" y2="200" />
          <line x1="90" y1="122" x2="90" y2="200" />
        </g>
        <rect x="76" y="104" width="28" height="20" rx="3" className="fill-primary" />
        <circle cx="104" cy="114" r="5" className="fill-primary-foreground" />
        {/* Altura */}
        <g className="stroke-muted-foreground" strokeWidth="1.5">
          <line x1="40" y1="114" x2="40" y2="200" />
          <line x1="34" y1="114" x2="46" y2="114" />
          <line x1="34" y1="200" x2="46" y2="200" />
        </g>
        <text x="30" y="160" textAnchor="end" className="fill-foreground text-[13px]">90–100 cm</text>
        {/* Distancia */}
        <g className="stroke-muted-foreground" strokeWidth="1.5">
          <line x1="110" y1="218" x2="505" y2="218" />
          <line x1="110" y1="212" x2="110" y2="224" />
          <line x1="505" y1="212" x2="505" y2="224" />
        </g>
        <rect x="262" y="208" width="92" height="20" className="fill-background" />
        <text x="308" y="223" textAnchor="middle" className="fill-foreground text-[13px] font-medium">2,5–3 m</text>
        {/* Campo de visión */}
        <path d="M106 114 L560 14 L560 206 Z" className="fill-primary/8 stroke-primary/40" strokeDasharray="5 5" />
        <text x="520" y="14" textAnchor="middle" className="fill-muted-foreground text-[12px]">cuerpo entero con margen</text>
      </svg>
      <figcaption className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
        <CheckCircle2 className="size-4 text-primary" aria-hidden="true" />
        Repita la misma distancia, altura y lugar en cada control para que las evaluaciones sean comparables.
      </figcaption>
    </figure>
  );
}
