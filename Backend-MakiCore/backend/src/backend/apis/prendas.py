from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from backend.apis.dependencies import ArtesanoActual
from backend.schemas.prendas import Prenda, PrendaCreate
from backend.services.prendas import PrendaService, prenda_service

router = APIRouter(prefix="/prendas", tags=["prendas"])

PrendaIdPath = Annotated[
    str,
    Path(min_length=1, max_length=40, description="Id de la prenda (código QR)."),
]


def get_prenda_service() -> PrendaService:
    return prenda_service


ServiceDep = Annotated[PrendaService, Depends(get_prenda_service)]


@router.get("", response_model=list[Prenda], summary="Listar el catálogo")
def listar_catalogo(
    service: ServiceDep,
    fibra: Annotated[
        str | None, Query(description='Filtra por fibra; "Todas" no filtra.')
    ] = None,
) -> list[Prenda]:
    return service.listar(fibra)


# Debe ir antes de /{prenda_id}; si no, "mias" se interpretaría como un id.
@router.get("/mias", response_model=list[Prenda], summary="Listar mis prendas (artesano)")
def listar_mis_prendas(artesano: ArtesanoActual, service: ServiceDep) -> list[Prenda]:
    return service.listar_de_artesano(artesano)


@router.get("/{prenda_id}", response_model=Prenda, summary="Obtener una prenda")
def obtener_prenda(prenda_id: PrendaIdPath, service: ServiceDep) -> Prenda:
    return service.obtener(prenda_id)


@router.post(
    "",
    response_model=Prenda,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una prenda (artesano)",
)
def registrar_prenda(
    datos: PrendaCreate, artesano: ArtesanoActual, service: ServiceDep
) -> Prenda:
    """El `id` devuelto es el código del QR (MAKI-0001...)."""
    return service.registrar(artesano, datos)
