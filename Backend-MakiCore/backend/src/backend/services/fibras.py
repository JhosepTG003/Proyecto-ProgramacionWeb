from threading import Lock

from backend.repositories.fibras import FibraRepository, fibra_repository
from backend.schemas.fibras import Fibra
from backend.services.exceptions import FibraAlreadyExistsError
from backend.validators import normalizar_fibra


class FibraService:
    """Reglas de negocio de las fibras."""

    def __init__(self, repository: FibraRepository | None = None) -> None:
        self._repository = repository or fibra_repository
        self._lock = Lock()

    def listar(self) -> list[Fibra]:
        return self._repository.list()

    def agregar(self, nombre: str) -> Fibra:
        """Crea una fibra nueva; si ya existe (sin importar mayúsculas ni tildes) avisa cuál."""
        normalizada = normalizar_fibra(nombre)
        with self._lock:
            existente = self._repository.get_by_nombre(normalizada)
            if existente:
                raise FibraAlreadyExistsError(existente.nombre)
            return self._repository.add(normalizada)

    def obtener_o_crear(self, nombre: str) -> Fibra:
        """Uso interno: al registrar una prenda con una fibra que no estaba, se agrega."""
        normalizada = normalizar_fibra(nombre)
        with self._lock:
            return self._repository.get_by_nombre(normalizada) or self._repository.add(normalizada)


fibra_service = FibraService()
