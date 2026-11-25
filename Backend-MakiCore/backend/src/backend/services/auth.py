from threading import Lock

from backend import config
from backend.repositories.sesiones import SesionRepository, sesion_repository
from backend.repositories.usuarios import UsuarioRepository, usuario_repository
from backend.schemas.auth import LoginIn, RegistroIn, TokenOut
from backend.schemas.enums import Rol
from backend.schemas.usuarios import Usuario, UsuarioOut
from backend.security import generar_token, hash_clave, hash_falso, verificar_clave
from backend.services.exceptions import (
    InvalidCredentialsError,
    NotAuthenticatedError,
    UsuarioAlreadyExistsError,
)


class AuthService:
    """Registro, inicio de sesión y sesiones."""

    def __init__(
        self,
        usuarios: UsuarioRepository | None = None,
        sesiones: SesionRepository | None = None,
    ) -> None:
        self._usuarios = usuarios or usuario_repository
        self._sesiones = sesiones or sesion_repository
        self._lock = Lock()  # revisar el correo y crear la cuenta debe ser un solo paso

    def registrar(self, datos: RegistroIn) -> Usuario:
        clave_hash = hash_clave(datos.clave)  # lento a propósito: se hace fuera del candado
        with self._lock:
            if self._usuarios.exists_correo(datos.correo):
                raise UsuarioAlreadyExistsError(datos.correo)

            artesano_id = None
            nombre_publico = None
            if datos.rol == Rol.ARTESANO:
                artesano_id = self._usuarios.siguiente_artesano_id()
                # Nombre público provisional, igual que el frontend: nunca se usa el correo.
                nombre_publico = f"Artesano {artesano_id}"

            return self._usuarios.add(
                Usuario(
                    correo=datos.correo,
                    clave_hash=clave_hash,
                    rol=datos.rol,
                    artesano_id=artesano_id,
                    nombre_publico=nombre_publico,
                )
            )

    def autenticar(self, datos: LoginIn) -> Usuario:
        usuario = self._usuarios.get_by_correo(datos.correo)
        if usuario is None:
            verificar_clave(datos.clave, hash_falso())  # mismo costo que un intento real
            raise InvalidCredentialsError()
        if not verificar_clave(datos.clave, usuario.clave_hash):
            raise InvalidCredentialsError()
        return usuario

    def crear_sesion(self, usuario: Usuario) -> TokenOut:
        token = generar_token()
        vigencia = config.SESION_MINUTOS * 60
        self._sesiones.add(token, usuario.id, vigencia)
        return TokenOut(
            access_token=token,
            expira_en=vigencia,
            usuario=UsuarioOut.model_validate(usuario, from_attributes=True),
        )

    def usuario_desde_token(self, token: str) -> Usuario:
        usuario_id = self._sesiones.get_usuario_id(token)
        usuario = self._usuarios.get(usuario_id) if usuario_id is not None else None
        if usuario is None:
            raise NotAuthenticatedError("Tu sesión no es válida o venció. Inicia sesión de nuevo.")
        return usuario

    def cerrar_sesion(self, token: str) -> None:
        self._sesiones.delete(token)


auth_service = AuthService()
