from fastapi import APIRouter, status

from backend.apis.dependencies import AuthServiceDep, TokenActual, UsuarioActual
from backend.schemas.auth import LoginIn, RegistroIn, TokenOut
from backend.schemas.usuarios import UsuarioOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/registro",
    response_model=TokenOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una cuenta",
)
def registro(datos: RegistroIn, service: AuthServiceDep) -> TokenOut:
    """Crea la cuenta con el rol elegido y deja la sesión iniciada."""
    return service.crear_sesion(service.registrar(datos))


@router.post("/login", response_model=TokenOut, summary="Iniciar sesión")
def login(datos: LoginIn, service: AuthServiceDep) -> TokenOut:
    """El rol lo asigna el servidor según la cuenta; el cliente no lo elige."""
    return service.crear_sesion(service.autenticar(datos))


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar sesión",
)
def logout(token: TokenActual, service: AuthServiceDep) -> None:
    service.usuario_desde_token(token)  # exige una sesión válida
    service.cerrar_sesion(token)


@router.get("/me", response_model=UsuarioOut, summary="Usuario con sesión iniciada")
def me(usuario: UsuarioActual) -> UsuarioOut:
    return UsuarioOut.model_validate(usuario, from_attributes=True)
