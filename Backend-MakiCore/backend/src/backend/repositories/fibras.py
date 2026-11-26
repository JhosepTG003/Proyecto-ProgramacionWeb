from backend import config
from backend.schemas.fibras import Fibra
from backend.validators import clave_fibra


class FibraRepository:
    """Almacenamiento de fibras en memoria, indexado por clave (nombre sin tildes ni
    mayúsculas), lo que impide duplicados como "Vicuña" y "vicuna"."""

    def __init__(self) -> None:
        self._fibras: dict[str, Fibra] = {}
        self._siguiente_id = 1

    def list(self) -> list[Fibra]:
        return list(self._fibras.values())

    def get_by_nombre(self, nombre: str) -> Fibra | None:
        return self._fibras.get(clave_fibra(nombre))

    def add(self, nombre: str) -> Fibra:
        fibra = Fibra(id=self._siguiente_id, nombre=nombre)
        self._siguiente_id += 1
        self._fibras[clave_fibra(nombre)] = fibra
        return fibra


if config.DATABASE_URL:
    from backend.repositories.postgres import PgFibraRepository

    fibra_repository = PgFibraRepository()
else:
    fibra_repository = FibraRepository()
