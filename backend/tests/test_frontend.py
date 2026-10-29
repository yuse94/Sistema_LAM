"""La API sirve la interfaz compilada: un solo proceso para el uso local."""
from fastapi.testclient import TestClient

from app.main import app


def test_serves_compiled_frontend_and_spa_routes():
    with TestClient(app) as c:
        home = c.get("/")
        assert home.status_code == 200 and "Sistema LAM" in home.text
        assert "Sistema LAM" in c.get("/pacientes/3").text  # ruta de React -> index.html
        js = c.get("/assets/app.js")
        assert js.status_code == 200 and "immutable" in js.headers["cache-control"]
        assert c.get("/mediapipe/vision.wasm").headers["content-type"] == "application/wasm"
        assert c.get("/api/no-existe").status_code == 404
        assert c.get("/api/health").json() == {"status": "ok"}
        for path in ("/../lam.db", "/%2e%2e/lam.db", "/..%2flam.db"):
            r = c.get(path)
            assert b"SQLite" not in r.content  # nunca sirve archivos fuera de la carpeta de la interfaz
