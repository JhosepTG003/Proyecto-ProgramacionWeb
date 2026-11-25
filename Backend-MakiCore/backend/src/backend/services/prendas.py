from threading import Lock

from backend.repositories.prendas import PrendaRepository, prenda_repository
from backend.schemas.prendas import Prenda, PrendaCreate
from backend.schemas.usuarios import Usuario
from backend.services.exceptions import PrendaNotFoundError
from backend.services.fibras import FibraService, fibra_service


class PrendaService:
    """Reglas de negocio del catálogo."""

    def __init__(
        self,
        repository: PrendaRepository | None = None,
        fibras: FibraService | None = None,
    ) -> None:
        self._repository = repository or prenda_repository
        self._fibras = fibras or fibra_service
        self._lock = Lock()  # generar el código y guardar la prenda debe ser un solo paso

    def listar(self, fibra: str | None = None) -> list[Prenda]:
        """Catálogo público. fibra=None (o "Todas") no filtra."""
        return self._repository.list(fibra=None if fibra in (None, "", "Todas") else fibra)

    def listar_de_artesano(self, artesano: Usuario) -> list[Prenda]:
        return self._repository.list(artesano_id=artesano.artesano_id)

    def obtener(self, prenda_id: str) -> Prenda:
        prenda = self._repository.get(prenda_id)
        if prenda is None:
            raise PrendaNotFoundError(prenda_id)
        return prenda

    def registrar(self, artesano: Usuario, datos: PrendaCreate) -> Prenda:
        """Registra la prenda a nombre del artesano con sesión iniciada (nunca de otro).
        Si la fibra no estaba en la lista, se agrega."""
        fibra = self._fibras.obtener_o_crear(datos.fibra)
        with self._lock:
            return self._repository.add(
                Prenda(
                    id=self._repository.siguiente_codigo(),
                    nombre=datos.nombre,
                    artesano=artesano.nombre_publico or "",
                    artesano_id=artesano.artesano_id or "",
                    fibra=fibra.nombre,
                    tinte=datos.tinte,
                    precio_centavos_usd=datos.precio_centavos_usd,
                    stock=datos.stock,
                    foto=datos.foto,
                )
            )


prenda_service = PrendaService()
