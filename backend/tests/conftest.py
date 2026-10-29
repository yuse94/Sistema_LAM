"""Las pruebas usan una base de datos y una carpeta de archivos temporales.

Se configura antes de importar la app: la sesión de SQLAlchemy se crea al importar.
"""
import os
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="lam_tests_"))
os.environ["LAM_DATABASE_URL"] = f"sqlite:///{(_tmp / 'lam.db').as_posix()}"
os.environ["LAM_STORAGE_DIR"] = str(_tmp / "storage")
