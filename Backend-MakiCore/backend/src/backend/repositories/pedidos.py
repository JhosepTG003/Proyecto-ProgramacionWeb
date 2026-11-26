from backend import config
from backend.schemas.pedidos import Pedido, PedidoItem


class PedidoRepository:
    """Almacenamiento de pedidos en memoria, indexado por id."""

    def __init__(self) -> None:
        self._pedidos: dict[int, Pedido] = {}
        self._siguiente_id = 1

    def get(self, pedido_id: int) -> Pedido | None:
        return self._pedidos.get(pedido_id)

    def add(self, pedido: Pedido) -> Pedido:
        pedido.id = self._siguiente_id
        self._siguiente_id += 1
        self._pedidos[pedido.id] = pedido
        return pedido

    def list_by_comprador(self, comprador_id: int) -> list[Pedido]:
        """Del más reciente al más antiguo."""
        propios = [p for p in self._pedidos.values() if p.comprador_id == comprador_id]
        return sorted(propios, key=lambda p: p.id, reverse=True)

    def list_items_de_artesano(self, artesano_id: str) -> list[tuple[Pedido, PedidoItem]]:
        """Líneas vendidas de un artesano, junto a su pedido, de la más reciente a la más antigua."""
        ventas = [
            (pedido, item)
            for pedido in self._pedidos.values()
            for item in pedido.items
            if item.artesano_id == artesano_id
        ]
        return sorted(ventas, key=lambda par: par[0].id, reverse=True)


if config.DATABASE_URL:
    from backend.repositories.sqlserver import SqlServerPedidoRepository

    pedido_repository = SqlServerPedidoRepository()
else:
    pedido_repository = PedidoRepository()
