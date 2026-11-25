import os

# Debe fijarse ANTES de importar la app: la configuración se lee al importarla.
os.environ["SEED_DEMO_DATA"] = "true"
os.environ["DEMO_PASSWORD"] = "maki123"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    # El "with" ejecuta el arranque, que carga los datos de ejemplo en memoria.
    with TestClient(app) as c:
        yield c


def _cabeceras(client: TestClient, correo: str, clave: str = "maki123") -> dict:
    r = client.post("/auth/login", json={"correo": correo, "clave": clave})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def comprador(client):
    return _cabeceras(client, "comprador@maki.pe")


@pytest.fixture(scope="session")
def artesano(client):
    return _cabeceras(client, "taller.godino@maki.pe")
