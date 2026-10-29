import { NavLink, Route, Routes } from "react-router";
import { cn } from "@/lib/utils";
import Configuracion from "@/pages/Configuracion";
import EvaluacionDetalle from "@/pages/EvaluacionDetalle";
import NuevaEvaluacion from "@/pages/NuevaEvaluacion";
import PacienteDetalle from "@/pages/PacienteDetalle";
import Pacientes from "@/pages/Pacientes";
import Puntos from "@/pages/Puntos";

const links = [
  { to: "/", label: "Evaluación" },
  { to: "/puntos", label: "Puntos" },
  { to: "/pacientes", label: "Pacientes" },
  { to: "/configuracion", label: "Configuración" },
];

/** Plomada: la referencia vertical con la que se mide la postura. */
function PlumbMark() {
  return (
    <svg viewBox="0 0 20 32" className="h-7 w-auto text-primary" aria-hidden="true">
      <line x1="10" y1="1" x2="10" y2="19" stroke="currentColor" strokeWidth="1.5" />
      <path d="M10 18 C6 22 5.5 25 7 27.5 C8 29.5 12 29.5 13 27.5 C14.5 25 14 22 10 18 Z" fill="currentColor" />
    </svg>
  );
}

export default function App() {
  return (
    <div className="min-h-screen">
      <header className="border-b bg-card">
        <nav className="mx-auto flex max-w-7xl items-center gap-8 px-4 py-3 sm:px-6" aria-label="Principal">
          <div className="flex items-center gap-2.5">
            <PlumbMark />
            <div className="leading-tight">
              <div className="font-bold tracking-tight">Sistema LAM</div>
              <div className="text-xs text-muted-foreground">Evaluación postural</div>
            </div>
          </div>
          <div className="flex gap-1">
            {links.map((l) => (
              <NavLink key={l.to} to={l.to} end={l.to === "/"}
                className={({ isActive }) => cn(
                  "rounded-md px-3 py-1.5 text-sm transition-colors outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50",
                  isActive ? "bg-accent font-medium text-accent-foreground" : "text-muted-foreground hover:text-foreground",
                )}>
                {l.label}
              </NavLink>
            ))}
          </div>
        </nav>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8">
        <Routes>
          <Route path="/" element={<NuevaEvaluacion />} />
          <Route path="/puntos" element={<Puntos />} />
          <Route path="/pacientes" element={<Pacientes />} />
          <Route path="/pacientes/:id" element={<PacienteDetalle />} />
          <Route path="/evaluaciones/:id" element={<EvaluacionDetalle />} />
          <Route path="/configuracion" element={<Configuracion />} />
        </Routes>
      </main>
    </div>
  );
}
