import { NavLink, Route, Routes } from "react-router";
import Configuracion from "@/pages/Configuracion";
import NuevaEvaluacion from "@/pages/NuevaEvaluacion";
import Pacientes from "@/pages/Pacientes";

const links = [
  { to: "/", label: "Nueva evaluación" },
  { to: "/pacientes", label: "Pacientes" },
  { to: "/configuracion", label: "Configuración" },
];

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b bg-white">
        <nav className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-3">
          <span className="font-semibold">Sistema LAM</span>
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end
              className={({ isActive }) => (isActive ? "font-medium text-emerald-700" : "text-slate-600")}>
              {l.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Routes>
          <Route path="/" element={<NuevaEvaluacion />} />
          <Route path="/pacientes" element={<Pacientes />} />
          <Route path="/configuracion" element={<Configuracion />} />
        </Routes>
      </main>
    </div>
  );
}
