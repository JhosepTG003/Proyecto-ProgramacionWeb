"""Dependencias compartidas: sesión iniciada y control de rol."""
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.schemas.enums import Rol
from backend.schemas.usuarios import Usuario
from backend.services.auth import AuthService, auth_service
from backend.services.exceptions import ForbiddenRoleError, NotAuthenticatedError

# auto_error=False: así la falta de token también pasa por nuestros manejadores (401 uniforme).
esquema_bearer = HTTPBearer(auto_error=False, description="Token obtenido en /auth/login")


def get_auth_service() -> AuthService:
    return auth_service


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_token(
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(esquema_bearer)],
) -> str:
    if credenciales is None:
        raise NotAuthenticatedError()
    return credenciales.credentials


TokenActual = Annotated[str, Depends(get_token)]


def get_usuario_actual(token: TokenActual, service: AuthServiceDep) -> Usuario:
    return service.usuario_desde_token(token)


UsuarioActual = Annotated[Usuario, Depends(get_usuario_actual)]


def requiere_rol(rol: Rol) -> Callable[..., Usuario]:
    """El rol sale del usuario guardado en el servidor, no de lo que diga el cliente."""

    def dependencia(usuario: UsuarioActual) -> Usuario:
        if usuario.rol != rol:
            raise ForbiddenRoleError(rol.value)
        return usuario

    return dependencia


ArtesanoActual = Annotated[Usuario, Depends(requiere_rol(Rol.ARTESANO))]
CompradorActual = Annotated[Usuario, Depends(requiere_rol(Rol.COMPRADOR))]
