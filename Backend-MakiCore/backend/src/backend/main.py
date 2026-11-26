from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend import config, db
from backend.apis.auth import router as auth_router
from backend.apis.configuracion import router as configuracion_router
from backend.apis.fibras import router as fibras_router
from backend.apis.pedidos import router as pedidos_router
from backend.apis.prendas import router as prendas_router
from backend.seed import sembrar_datos_demo
from backend.services.exceptions import (
    CantidadMaximaError,
    FibraAlreadyExistsError,
    ForbiddenRoleError,
    InvalidCredentialsError,
    NotAuthenticatedError,
    PedidoNotFoundError,
    PrendaAgotadaError,
    PrendaNotFoundError,
    StockInsuficienteError,
    UsuarioAlreadyExistsError,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if config.SEED_DEMO_DATA:
        sembrar_datos_demo()
    yield
    if config.DATABASE_URL:
        db.cerrar_pool()


app = FastAPI(
    title="Maki Core API",
    version="0.1.0",
    description="Backend de la tienda de artesanías textiles (SQL Server si hay DATABASE_URL; si no, memoria).",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(prendas_router)
app.include_router(fibras_router)
app.include_router(pedidos_router)
app.include_router(configuracion_router)


@app.get("/salud", tags=["estado"], summary="Estado del servidor")
def salud() -> dict[str, str]:
    return {"estado": "ok"}


# Cada excepción de negocio se traduce a su código HTTP, con el formato {"detail": "..."}
# que FastAPI usa también para sus propios errores.
ERRORES_HTTP: dict[type[Exception], int] = {
    NotAuthenticatedError: status.HTTP_401_UNAUTHORIZED,
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
    ForbiddenRoleError: status.HTTP_403_FORBIDDEN,
    PrendaNotFoundError: status.HTTP_404_NOT_FOUND,
    PedidoNotFoundError: status.HTTP_404_NOT_FOUND,
    UsuarioAlreadyExistsError: status.HTTP_409_CONFLICT,
    FibraAlreadyExistsError: status.HTTP_409_CONFLICT,
    PrendaAgotadaError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    StockInsuficienteError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    CantidadMaximaError: status.HTTP_422_UNPROCESSABLE_ENTITY,
}


def _crear_manejador(codigo: int) -> Callable[[Request, Exception], Awaitable[JSONResponse]]:
    async def manejador(request: Request, exc: Exception) -> JSONResponse:
        cabeceras = {"WWW-Authenticate": "Bearer"} if codigo == status.HTTP_401_UNAUTHORIZED else None
        return JSONResponse(status_code=codigo, content={"detail": str(exc)}, headers=cabeceras)

    return manejador


for _tipo, _codigo in ERRORES_HTTP.items():
    app.add_exception_handler(_tipo, _crear_manejador(_codigo))
