from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.config import MAX_CANTIDAD_POR_PRENDA
from backend.schemas.enums import EstadoPedido, Moneda, Zona
from backend.schemas.prendas import Prenda


class ItemPedidoIn(BaseModel):
    prenda_id: str = Field(..., min_length=1, max_length=40, examples=["poncho-andino"])
    cantidad: int = Field(..., ge=1, le=MAX_CANTIDAD_POR_PRENDA, examples=[2])


class PedidoIn(BaseModel):
    """El carrito vive en el frontend; al cotizar o pagar se envía su contenido."""

    items: list[ItemPedidoIn] = Field(..., min_length=1, max_length=50)
    moneda: Moneda = Moneda.USD
    zona: Zona = Zona.AMERICA


class LineaCotizacion(BaseModel):
    prenda: Prenda
    cantidad: int
    precio: int  # unitario, en centavos de la moneda elegida
    subtotal: int


class Cotizacion(BaseModel):
    moneda: Moneda
    zona: Zona
    lineas: list[LineaCotizacion]
    total_prendas: int
    subtotal: int
    envio: int
    total: int
    plataforma: int  # 20 % del subtotal (el envío no entra en la división)
    cooperativa: int  # 80 % del subtotal


class PedidoItem(BaseModel):
    """Línea de un pedido. Guarda una copia del nombre y del precio al momento de la compra."""

    prenda_id: str
    artesano_id: str
    nombre_prenda: str
    cantidad: int
    precio_unitario: int
    subtotal: int


class PedidoBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = 0  # lo asigna el repositorio
    estado: EstadoPedido
    moneda: Moneda
    zona: Zona
    items: list[PedidoItem]
    subtotal: int
    envio: int
    total: int
    plataforma: int
    cooperativa: int
    creado_en: datetime


class Pedido(PedidoBase):
    """Pedido almacenado (pagado). Los montos están en centavos de la moneda elegida."""

    comprador_id: int


class PedidoOut(PedidoBase):
    """Lo que ve el comprador: sin datos internos."""

    mensaje: str | None = None  # solo al crear el pedido


class Venta(BaseModel):
    """Una línea vendida, tal como la ve el artesano dueño de la prenda."""

    pedido_id: int
    fecha: datetime
    prenda_id: str
    nombre_prenda: str
    cantidad: int
    precio_unitario: int
    subtotal: int
    moneda: Moneda
