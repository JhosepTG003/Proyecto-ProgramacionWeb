import time

from backend import config


class SesionRepository:
    """Sesiones iniciadas, en memoria: token -> (id de usuario, momento en que vence)."""

    def __init__(self) -> None:
        self._sesiones: dict[str, tuple[int, float]] = {}

    def add(self, token: str, usuario_id: int, vigencia_segundos: int) -> None:
        self._limpiar_vencidas()
        self._sesiones[token] = (usuario_id, time.time() + vigencia_segundos)

    def get_usuario_id(self, token: str) -> int | None:
        """Devuelve el usuario dueño del token, o None si no existe o ya venció."""
        sesion = self._sesiones.get(token)
        if sesion is None:
            return None
        usuario_id, vence = sesion
        if vence <= time.time():
            self._sesiones.pop(token, None)
            return None
        return usuario_id

    def delete(self, token: str) -> bool:
        return self._sesiones.pop(token, None) is not None

    def _limpiar_vencidas(self) -> None:
        ahora = time.time()
        for token in [t for t, (_, vence) in self._sesiones.items() if vence <= ahora]:
            self._sesiones.pop(token, None)


if config.DATABASE_URL:
    from backend.repositories.sqlserver import SqlServerSesionRepository

    sesion_repository = SqlServerSesionRepository()
else:
    sesion_repository = SesionRepository()
