from __future__ import annotations

from collections.abc import Collection

from backend import config
from backend.schemas.prendas import Prenda
from backend.validators import clave_fibra

PREFIJO_CODIGO = "MAKI-"


class PrendaRepository:
    """Almacenamiento de prendas en memoria, indexado por id (el código del QR)."""

    def __init__(self) -> None:
        self._prendas: dict[str, Prenda] = {}

    def list(self, fibra: str | None = None, artesano_id: str | None = None) -> list[Prenda]:
        prendas = list(self._prendas.values())
        if fibra:
            clave = clave_fibra(fibra)
            prendas = [p for p in prendas if clave_fibra(p.fibra) == clave]
        if artesano_id:
            prendas = [p for p in prendas if p.artesano_id == artesano_id]
        return prendas

    def get(self, prenda_id: str) -> Prenda | None:
        return self._prendas.get(prenda_id)

    def get_many(self, ids: Collection[str]) -> list[Prenda]:
        return [self._prendas[i] for i in ids if i in self._prendas]

    def siguiente_codigo(self) -> str:
        """MAKI-0001, MAKI-0002... El siguiente a partir del mayor existente."""
        numeros = [
            int(i[len(PREFIJO_CODIGO):])
            for i in self._prendas
            if i.startswith(PREFIJO_CODIGO) and i[len(PREFIJO_CODIGO):].isdigit()
        ]
        return f"{PREFIJO_CODIGO}{max(numeros, default=0) + 1:04d}"

    def add(self, prenda: Prenda) -> Prenda:
        self._prendas[prenda.id] = prenda
        return prenda

    def descontar_stock(self, prenda_id: str, cantidad: int) -> bool:
        """Descuenta stock solo si alcanza. Devuelve False si no (el stock nunca queda negativo).
        El service la llama dentro de un candado para que sea atómica entre peticiones."""
        prenda = self._prendas.get(prenda_id)
        if prenda is None or prenda.stock < cantidad:
            return False
        prenda.stock -= cantidad
        return True


if config.DATABASE_URL:
    from backend.repositories.sqlserver import SqlServerPrendaRepository

    prenda_repository = SqlServerPrendaRepository()
else:
    prenda_repository = PrendaRepository()
