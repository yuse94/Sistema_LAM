import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from tests.synthetic import ANTERIOR, make_image


def _png(points):
    buf = io.BytesIO()
    Image.fromarray(make_image(points)).save(buf, format="PNG")
    return buf.getvalue()


def test_health_and_defaults():
    with TestClient(app) as c:
        assert c.get("/api/health").json() == {"status": "ok"}
        assert c.get("/api/config/defaults").json()["filter_threshold"] == 0.32


def test_analysis_endpoint_ok():
    with TestClient(app) as c:
        r = c.post("/api/analysis/anterior", files={"file": ("a.png", _png(ANTERIOR), "image/png")},
                   params={"tolerance_angle": 1, "tolerance_distance": 1})
        assert r.status_code == 200, r.text
        body = r.json()
        assert len(body["tables"]) == 3
        assert body["image"].startswith("data:image/jpeg;base64,")

        # El evaluador baja el hombro izquierdo (F4) y recalcula sin volver a subir la foto
        landmarks = body["markers"]
        landmarks["F4"]["y"] += 30
        r2 = c.post("/api/analysis/anterior/evaluate",
                    json={"landmarks": landmarks, "scale_ratio": body["scale_ratio"],
                          "config": {"tolerance_angle": 1, "tolerance_distance": 1}})
        assert r2.status_code == 200, r2.text
        assert r2.json()["tables"][0]["rows"][0]["direction"] == "Izq."


def test_views_catalog_includes_left_lateral():
    with TestClient(app) as c:
        views = {v["view"]: v for v in c.get("/api/analysis/views").json()}
        assert set(views) == {"anterior", "posterior", "lateral_derecha", "lateral_izquierda"}
        assert views["anterior"]["labels"]["F1"] == "Entrecejo"


def test_analysis_endpoint_marker_error():
    with TestClient(app) as c:
        r = c.post("/api/analysis/anterior", files={"file": ("a.png", _png(ANTERIOR[:5]), "image/png")})
        assert r.status_code == 422
        assert r.json()["found"] == 5


def test_patients_crud():
    with TestClient(app) as c:
        r = c.post("/api/patients", json={"name": "  juan perez ", "age": 30, "gender": "M"})
        assert r.status_code == 201
        assert r.json()["name"] == "Juan Perez"
        assert any(p["name"] == "Juan Perez" for p in c.get("/api/patients").json())
