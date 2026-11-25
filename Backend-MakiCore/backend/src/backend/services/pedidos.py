from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock

from backend.config import MAX_CANTIDAD_POR_PRENDA, MENSAJE_PAGO_APROBADO
from backend.repositories.pedidos import PedidoRepository, pedido_repository
from backend.repositories.prendas import PrendaRepository, prenda_repository
from backend.schemas.enums import EstadoPedido
from backend.schemas.pedidos import (
    Cotizacion,
    LineaCotizacion,
    Pedido,
    PedidoIn,
    PedidoItem,
    PedidoOut,
    Venta,
)
from backend.schemas.prendas import Prenda
from backend.schemas.usuarios import Usuario
from backend.services.dinero import convertir, costo_envio, dividir_venta
from backend.services.exceptions import (
    CantidadMaximaError,
    PedidoNotFoundError,
    PrendaAgotadaError,
    PrendaNotFoundError,
    StockInsuficienteError,
)


@dataclass
class _Linea:
    prenda: Prenda
    cantidad: int
    precio: int  # unitario, centavos de la moneda elegida
    subtotal: int


@dataclass
class _Calculo:
    lineas: list[_Linea]
    subtotal: int
    envio: int
    total: int
    plataforma: int
    cooperativa: int


class PedidoService:
    """Reglas de negocio del carrito, el pago y los pedidos."""

    def __init__(
        self,
        prendas: PrendaRepository | None = None,
        pedidos: PedidoRepository | None = None,
    ) -> None:
        self._prendas = prendas or prenda_repository
        self._pedidos = pedidos or pedido_repository
        self._lock = Lock()  # validar el stock y descontarlo debe ser un solo paso

    # ---------- Cálculo (compartido por cotizar y pagar) ----------
    @staticmethod
    def _validar_cantidad(prenda: Prenda, cantidad: int) -> None:
        """Lanza el error que corresponda si NO se puede pedir esa cantidad."""
        if prenda.stock <= 0:
            raise PrendaAgotadaError(prenda.nombre)
        if cantidad > prenda.stock:
            raise StockInsuficienteError(prenda.nombre, prenda.stock)
        if cantidad > MAX_CANTIDAD_POR_PRENDA:
            raise CantidadMaximaError(prenda.nombre, MAX_CANTIDAD_POR_PRENDA)

    def _calcular(self, datos: PedidoIn) -> _Calculo:
        # Si la misma prenda viene repetida se suman sus cantidades.
        cantidades: dict[str, int] = {}
        for item in datos.items:
            cantidades[item.prenda_id] = cantidades.get(item.prenda_id, 0) + item.cantidad

        lineas: list[_Linea] = []
        for prenda_id in sorted(cantidades):
            prenda = self._prendas.get(prenda_id)
            if prenda is None:
                raise PrendaNotFoundError(prenda_id)
            cantidad = cantidades[prenda_id]
            self._validar_cantidad(prenda, cantidad)
            precio = convertir(prenda.precio_centavos_usd, datos.moneda)
            lineas.append(_Linea(prenda, cantidad, precio, cantidad * precio))

        subtotal = sum(linea.subtotal for linea in lineas)
        envio = costo_envio(subtotal, datos.zona, datos.moneda)
        plataforma, cooperativa = dividir_venta(subtotal)  # el envío no entra en la división
        return _Calculo(lineas, subtotal, envio, subtotal + envio, plataforma, cooperativa)

    # ---------- Casos de uso ----------
    def cotizar(self, datos: PedidoIn) -> Cotizacion:
        calculo = self._calcular(datos)
        return Cotizacion(
            moneda=datos.moneda,
            zona=datos.zona,
            lineas=[
                LineaCotizacion(
                    prenda=l.prenda, cantidad=l.cantidad, precio=l.precio, subtotal=l.subtotal
                )
                for l in calculo.lineas
            ],
            total_prendas=sum(l.cantidad for l in calculo.lineas),
            subtotal=calculo.subtotal,
            envio=calculo.envio,
            total=calculo.total,
            plataforma=calculo.plataforma,
            cooperativa=calculo.cooperativa,
        )

    def pagar(self, comprador: Usuario, datos: PedidoIn) -> PedidoOut:
        """Valida, descuenta el stock y registra el pedido. Todo ocurre dentro de un candado:
        dos pagos simultáneos nunca se llevan el mismo stock."""
        with self._lock:
            calculo = self._calcular(datos)
            for linea in calculo.lineas:
                # Ya se validó dentro del candado, así que no puede fallar; se revisa por seguridad.
                if not self._prendas.descontar_stock(linea.prenda.id, linea.cantidad):
                    raise StockInsuficienteError(linea.prenda.nombre, linea.prenda.stock)

            pedido = self._pedidos.add(
                Pedido(
                    comprador_id=comprador.id,
                    estado=EstadoPedido.APROBADO,
                    moneda=datos.moneda,
                    zona=datos.zona,
                    items=[
                        PedidoItem(
                            prenda_id=l.prenda.id,
                            artesano_id=l.prenda.artesano_id,
                            nombre_prenda=l.prenda.nombre,
                            cantidad=l.cantidad,
                            precio_unitario=l.precio,
                            subtotal=l.subtotal,
                        )
                        for l in calculo.lineas
                    ],
                    subtotal=calculo.subtotal,
                    envio=calculo.envio,
                    total=calculo.total,
                    plataforma=calculo.plataforma,
                    cooperativa=calculo.cooperativa,
                    creado_en=datetime.now(timezone.utc),
                )
            )
        salida = PedidoOut.model_validate(pedido, from_attributes=True)
        return salida.model_copy(update={"mensaje": MENSAJE_PAGO_APROBADO})

    def listar_de_comprador(self, comprador: Usuario) -> list[PedidoOut]:
        return [
            PedidoOut.model_validate(p, from_attributes=True)
            for p in self._pedidos.list_by_comprador(comprador.id)
        ]

    def obtener_de_comprador(self, comprador: Usuario, pedido_id: int) -> PedidoOut:
        pedido = self._pedidos.get(pedido_id)
        # Un pedido ajeno se responde igual que uno inexistente: no se revela que existe.
        if pedido is None or pedido.comprador_id != comprador.id:
            raise PedidoNotFoundError(pedido_id)
        return PedidoOut.model_validate(pedido, from_attributes=True)

    def ventas_de_artesano(self, artesano: Usuario) -> list[Venta]:
        return [
            Venta(
                pedido_id=pedido.id,
                fecha=pedido.creado_en,
                prenda_id=item.prenda_id,
                nombre_prenda=item.nombre_prenda,
                cantidad=item.cantidad,
                precio_unitario=item.precio_unitario,
                subtotal=item.subtotal,
                moneda=pedido.moneda,
            )
            for pedido, item in self._pedidos.list_items_de_artesano(artesano.artesano_id or "")
        ]


pedido_service = PedidoService()
