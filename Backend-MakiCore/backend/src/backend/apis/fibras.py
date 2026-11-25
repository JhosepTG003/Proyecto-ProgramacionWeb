from typing import Annotated

from fastapi import APIRouter, Depends, status

from backend.apis.dependencies import ArtesanoActual
from backend.schemas.fibras import Fibra, FibraCreate
from backend.services.fibras import FibraService, fibra_service

router = APIRouter(prefix="/fibras", tags=["fibras"])


def get_fibra_service() -> FibraService:
    return fibra_service


ServiceDep = Annotated[FibraService, Depends(get_fibra_service)]


@router.get("", response_model=list[Fibra], summary="Listar fibras")
def listar_fibras(service: ServiceDep) -> list[Fibra]:
    """Alimenta el selector del formulario y los filtros del catálogo."""
    return service.listar()


@router.post(
    "",
    response_model=Fibra,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar una fibra (artesano)",
)
def agregar_fibra(
    datos: FibraCreate, artesano: ArtesanoActual, service: ServiceDep
) -> Fibra:
    return service.agregar(datos.nombre)
