from backend import config
from backend.schemas.usuarios import Usuario


class UsuarioRepository:
    """Almacenamiento de usuarios en memoria, indexado por id.

    Los datos viven durante la vida del proceso: se pierden al reiniciar el servidor.
    """

    def __init__(self) -> None:
        self._usuarios: dict[int, Usuario] = {}
        self._por_correo: dict[str, int] = {}
        self._siguiente_id = 1

    def list(self) -> list[Usuario]:
        return list(self._usuarios.values())

    def get(self, usuario_id: int) -> Usuario | None:
        return self._usuarios.get(usuario_id)

    def get_by_correo(self, correo: str) -> Usuario | None:
        usuario_id = self._por_correo.get(correo)
        return self._usuarios.get(usuario_id) if usuario_id is not None else None

    def exists_correo(self, correo: str) -> bool:
        return correo in self._por_correo

    def siguiente_artesano_id(self) -> str:
        """ART-0001, ART-0002... El siguiente a partir del mayor existente."""
        numeros = [
            int(u.artesano_id.split("-")[1]) for u in self._usuarios.values() if u.artesano_id
        ]
        return f"ART-{max(numeros, default=0) + 1:04d}"

    def add(self, usuario: Usuario) -> Usuario:
        usuario.id = self._siguiente_id
        self._siguiente_id += 1
        self._usuarios[usuario.id] = usuario
        self._por_correo[usuario.correo] = usuario.id
        return usuario


if config.DATABASE_URL:
    from backend.repositories.postgres import PgUsuarioRepository

    usuario_repository = PgUsuarioRepository()
else:
    usuario_repository = UsuarioRepository()
