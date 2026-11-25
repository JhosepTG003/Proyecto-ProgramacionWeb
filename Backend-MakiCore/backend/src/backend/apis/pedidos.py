from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from backend.apis.dependencies import ArtesanoActual, CompradorActual
from backend.schemas.pedidos import Cotizacion, PedidoIn, PedidoOut, Venta
from backend.services.pedidos import PedidoService, pedido_service

router = APIRouter(prefix="/pedidos", tags=["pedidos"])

PedidoIdPath = Annotated[int, Path(ge=1, description="Id del pedido.")]


def get_pedido_service() -> PedidoService:
    return pedido_service


ServiceDep = Annotated[PedidoService, Depends(get_pedido_service)]


@router.post("/cotizar", response_model=Cotizacion, summary="Cotizar el carrito")
def cotizar(datos: PedidoIn, service: ServiceDep) -> Cotizacion:
    """Subtotal, envío, total y división 20/80 sin cobrar ni tocar el stock.
    Es público, igual que el carrito del frontend."""
    return service.cotizar(datos)


@router.post(
    "",
    response_model=PedidoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Pagar el carrito (comprador)",
)
def pagar(datos: PedidoIn, comprador: CompradorActual, service: ServiceDep) -> PedidoOut:
    """Revisa y descuenta el stock y registra el pedido."""
    return service.pagar(comprador, datos)


@router.get("/mis-pedidos", response_model=list[PedidoOut], summary="Mis pedidos (comprador)")
def mis_pedidos(comprador: CompradorActual, service: ServiceDep) -> list[PedidoOut]:
    return service.listar_de_comprador(comprador)


@router.get("/ventas", response_model=list[Venta], summary="Mis ventas (artesano)")
def mis_ventas(artesano: ArtesanoActual, service: ServiceDep) -> list[Venta]:
    """Ventas de las prendas del artesano (la «notificación de venta» del pago)."""
    return service.ventas_de_artesano(artesano)


@router.get("/{pedido_id}", response_model=PedidoOut, summary="Obtener un pedido propio")
def obtener_pedido(
    pedido_id: PedidoIdPath, comprador: CompradorActual, service: ServiceDep
) -> PedidoOut:
    return service.obtener_de_comprador(comprador, pedido_id)
