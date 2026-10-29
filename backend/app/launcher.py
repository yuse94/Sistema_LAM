"""Arranque para usar la app en un equipo local (demostraciones, centros sin servidor).

Un solo proceso sirve la API y la interfaz compilada, y abre el navegador. Los datos
(base de datos, fotografías, datos del centro) quedan en la carpeta "datos" junto a la
app, fácil de respaldar o de borrar.

    uv run python -m app.launcher            (lo ejecuta "Iniciar LAM.bat")
"""
from __future__ import annotations

import os
import socket
import threading
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # carpeta del proyecto (contiene backend/ y frontend/)


def _free_port(start: int = 8000) -> int:
    for port in range(start, start + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("No hay puertos libres entre 8000 y 8049")


def main() -> None:
    data = Path(os.environ.get("LAM_DATA_DIR", ROOT / "datos")).resolve()
    data.mkdir(parents=True, exist_ok=True)
    # Antes de importar la app: la configuración se lee una sola vez
    os.environ.setdefault("LAM_DATABASE_URL", f"sqlite:///{(data / 'lam.db').as_posix()}")
    os.environ.setdefault("LAM_STORAGE_DIR", str(data / "archivos"))
    os.environ.setdefault("LAM_FRONTEND_DIR", str(ROOT / "frontend" / "dist"))

    if not (Path(os.environ["LAM_FRONTEND_DIR"]) / "index.html").is_file():
        raise SystemExit("Falta la interfaz compilada (frontend/dist). Ejecute 'npm run build' en frontend/ "
                         "o use el paquete generado por scripts/empaquetar.ps1.")

    port = int(os.environ.get("LAM_PORT") or _free_port())
    url = f"http://localhost:{port}"
    print("\n  Sistema LAM")
    print(f"  Abra {url} en el navegador (se abrirá solo).")
    print(f"  Datos: {data}")
    print("  Para cerrar la aplicación, cierre esta ventana o presione Ctrl+C.\n")
    if os.environ.get("LAM_NO_BROWSER") != "1":
        threading.Timer(2.0, webbrowser.open, [url]).start()

    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
