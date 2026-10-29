"""Las pruebas usan una base de datos y una carpeta de archivos temporales.

Se configura antes de importar la app: la sesión de SQLAlchemy se crea al importar.
"""
import os
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="lam_tests_"))
os.environ["LAM_DATABASE_URL"] = f"sqlite:///{(_tmp / 'lam.db').as_posix()}"
os.environ["LAM_STORAGE_DIR"] = str(_tmp / "storage")

# Interfaz compilada mínima, para probar que la API también la sirve (uso local)
_front = _tmp / "frontend"
(_front / "assets").mkdir(parents=True)
(_front / "mediapipe").mkdir()
(_front / "index.html").write_text("<!doctype html><title>Sistema LAM</title>", encoding="utf-8")
(_front / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
(_front / "mediapipe" / "vision.wasm").write_bytes(b"\0asm")
os.environ["LAM_FRONTEND_DIR"] = str(_front)
