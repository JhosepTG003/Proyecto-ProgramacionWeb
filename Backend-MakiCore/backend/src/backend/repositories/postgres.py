"""Repositorios sobre SQL Server. Tienen los mismos metodos que los de memoria, asi que los
services y las apis no cambian. Las tablas y vistas salen de database-MakiCore-sqlserver.sql.

Se conserva el nombre del archivo y de las clases (Pg...) para no tocar el resto del backend,
aunque ahora hablan con SQL Server.
"""

from __future__ import annotations

import hashlib
from collections.abc import Collection

from backend.db import conexion
from backend.schemas.fibras import Fibra
from backend.schemas.pedidos import Pedido, PedidoItem
from backend.schemas.prendas import Prenda
from backend.schemas.usuarios import Usuario
from backend.validators import clave_fibra


def _marcadores(cantidad: int) -> str:
    """'?, ?, ?' para armar un IN (...) con parametros."""
    return ", ".join("?" * cantidad)


# ---------------------------------------------------------------- usuarios
class PgUsuarioRepository:
    _COLUMNAS = "id, correo, clave_hash, rol, artesano_id, nombre_publico"

    def list(self) -> list[Usuario]:
        with conexion() as conn:
            filas = conn.execute(f"SELECT {self._COLUMNAS} FROM usuarios ORDER BY id").fetchall()
        return [Usuario(**f) for f in filas]

    def get(self, usuario_id: int) -> Usuario | None:
        with conexion() as conn:
            fila = conn.execute(
                f"SELECT {self._COLUMNAS} FROM usuarios WHERE id = ?", (usuario_id,)
            ).fetchone()
        return Usuario(**fila) if fila else None

    def get_by_correo(self, correo: str) -> Usuario | None:
        with conexion() as conn:
            fila = conn.execute(
                f"SELECT {self._COLUMNAS} FROM usuarios WHERE correo = ?", (correo,)
            ).fetchone()
        return Usuario(**fila) if fila else None

    def exists_correo(self, correo: str) -> bool:
        with conexion() as conn:
            fila = conn.execute("SELECT 1 AS ok FROM usuarios WHERE correo = ?", (correo,)).fetchone()
        return fila is not None

    def siguiente_artesano_id(self) -> str:
        """ART-0001, ART-0002... El siguiente a partir del mayor existente."""
        with conexion() as conn:
            fila = conn.execute(
                "SELECT COALESCE(MAX(TRY_CAST(SUBSTRING(artesano_id, 5, 20) AS INT)), 0) + 1 AS n "
                "FROM artesanos"
            ).fetchone()
        return f"ART-{fila['n']:04d}"

    def add(self, usuario: Usuario) -> Usuario:
        with conexion() as conn:
            conn.execute(
                "INSERT INTO usuarios (correo, clave_hash, rol, artesano_id, nombre_publico) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    usuario.correo,
                    usuario.clave_hash,
                    usuario.rol.value,
                    usuario.artesano_id,
                    usuario.nombre_publico,
                ),
            )
            # La tabla tiene un trigger INSTEAD OF INSERT: OUTPUT inserted.id vendria vacio.
            # Se consulta el usuario recien creado por su correo (que es unico).
            fila = conn.execute(
                "SELECT id FROM usuarios WHERE correo = ?", (usuario.correo,)
            ).fetchone()
        usuario.id = fila["id"]
        return usuario


# ---------------------------------------------------------------- sesiones
def _hash_token(token: str) -> str:
    """En la base solo se guarda el SHA-256 del token, nunca el token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class PgSesionRepository:
    def add(self, token: str, usuario_id: int, vigencia_segundos: int) -> None:
        with conexion() as conn:
            conn.execute("DELETE FROM sesiones WHERE expira_en <= SYSDATETIMEOFFSET()")
            conn.execute(
                "INSERT INTO sesiones (token_hash, usuario_id, expira_en) "
                "VALUES (?, ?, DATEADD(SECOND, ?, SYSDATETIMEOFFSET()))",
                (_hash_token(token), usuario_id, vigencia_segundos),
            )

    def get_usuario_id(self, token: str) -> int | None:
        with conexion() as conn:
            fila = conn.execute(
                "SELECT usuario_id FROM sesiones "
                "WHERE token_hash = ? AND expira_en > SYSDATETIMEOFFSET()",
                (_hash_token(token),),
            ).fetchone()
        return fila["usuario_id"] if fila else None

    def delete(self, token: str) -> bool:
        with conexion() as conn:
            cur = conn.execute("DELETE FROM sesiones WHERE token_hash = ?", (_hash_token(token),))
            return cur.rowcount > 0


# ------------------------------------------------------------------ fibras
class PgFibraRepository:
    def list(self) -> list[Fibra]:
        with conexion() as conn:
            filas = conn.execute("SELECT id, nombre FROM fibras ORDER BY id").fetchall()
        return [Fibra(**f) for f in filas]

    def get_by_nombre(self, nombre: str) -> Fibra | None:
        with conexion() as conn:
            fila = conn.execute(
                "SELECT id, nombre FROM fibras WHERE clave = ?", (clave_fibra(nombre),)
            ).fetchone()
        return Fibra(**fila) if fila else None

    def add(self, nombre: str) -> Fibra:
        with conexion() as conn:
            fila = conn.execute(
                "INSERT INTO fibras (nombre, clave) OUTPUT INSERTED.id VALUES (?, ?)",
                (nombre, clave_fibra(nombre)),
            ).fetchone()
        return Fibra(id=fila["id"], nombre=nombre)


# ----------------------------------------------------------------- prendas
class PgPrendaRepository:
    # La vista v_catalogo ya une prendas + artesano (nombre publico) + fibra.
    # SQL Server no permite ORDER BY dentro de la vista: el orden va en cada consulta.
    _SELECT = (
        "SELECT id, nombre, artesano, artesano_id, fibra, tinte, "
        "precio_centavos_usd, stock, foto FROM v_catalogo"
    )
    _ORDEN = "ORDER BY creado_en, id"

    def list(self, fibra: str | None = None, artesano_id: str | None = None) -> list[Prenda]:
        with conexion() as conn:
            if artesano_id:
                filas = conn.execute(
                    f"{self._SELECT} WHERE artesano_id = ? {self._ORDEN}", (artesano_id,)
                ).fetchall()
            else:
                filas = conn.execute(f"{self._SELECT} {self._ORDEN}").fetchall()
        prendas = [Prenda(**f) for f in filas]
        if fibra:
            clave = clave_fibra(fibra)
            prendas = [p for p in prendas if clave_fibra(p.fibra) == clave]
        return prendas

    def get(self, prenda_id: str) -> Prenda | None:
        with conexion() as conn:
            fila = conn.execute(f"{self._SELECT} WHERE id = ?", (prenda_id,)).fetchone()
        return Prenda(**fila) if fila else None

    def get_many(self, ids: Collection[str]) -> list[Prenda]:
        if not ids:
            return []
        lista = list(ids)
        with conexion() as conn:
            filas = conn.execute(
                f"{self._SELECT} WHERE id IN ({_marcadores(len(lista))}) {self._ORDEN}", lista
            ).fetchall()
        return [Prenda(**f) for f in filas]

    def siguiente_codigo(self) -> str:
        """MAKI-0001, MAKI-0002... El siguiente a partir del mayor existente."""
        with conexion() as conn:
            fila = conn.execute(
                "SELECT COALESCE(MAX(TRY_CAST(SUBSTRING(id, 6, 20) AS INT)), 0) + 1 AS n "
                "FROM prendas"
            ).fetchone()
        return f"MAKI-{fila['n']:04d}"

    def add(self, prenda: Prenda) -> Prenda:
        with conexion() as conn:
            conn.execute(
                "INSERT INTO prendas "
                "(id, nombre, tinte, precio_centavos_usd, stock, foto, artesano_id, fibra_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, (SELECT id FROM fibras WHERE clave = ?))",
                (
                    prenda.id,
                    prenda.nombre,
                    prenda.tinte,
                    prenda.precio_centavos_usd,
                    prenda.stock,
                    prenda.foto,
                    prenda.artesano_id,
                    clave_fibra(prenda.fibra),
                ),
            )
        return prenda

    def descontar_stock(self, prenda_id: str, cantidad: int) -> bool:
        """El UPDATE con 'stock >= cantidad' es atomico en la base: el stock nunca queda negativo."""
        with conexion() as conn:
            cur = conn.execute(
                "UPDATE prendas SET stock = stock - ? WHERE id = ? AND stock >= ?",
                (cantidad, prenda_id, cantidad),
            )
            return cur.rowcount == 1


# ----------------------------------------------------------------- pedidos
class PgPedidoRepository:
    _PEDIDO = (
        "SELECT id, comprador_id, estado, moneda, zona, subtotal, envio, total, "
        "plataforma, cooperativa, creado_en FROM pedidos"
    )

    @staticmethod
    def _armar(conn, filas: list[dict]) -> list[Pedido]:
        """Convierte filas de 'pedidos' en objetos Pedido, cargando sus lineas de una vez."""
        if not filas:
            return []
        items_por_pedido: dict[int, list[PedidoItem]] = {f["id"]: [] for f in filas}
        ids = list(items_por_pedido)
        lineas = conn.execute(
            "SELECT pedido_id, prenda_id, artesano_id, nombre_prenda, cantidad, "
            "precio_unitario, subtotal FROM pedido_items "
            f"WHERE pedido_id IN ({_marcadores(len(ids))}) ORDER BY id",
            ids,
        ).fetchall()
        for linea in lineas:
            pedido_id = linea.pop("pedido_id")
            items_por_pedido[pedido_id].append(PedidoItem(**linea))
        return [Pedido(items=items_por_pedido[f["id"]], **f) for f in filas]

    def get(self, pedido_id: int) -> Pedido | None:
        with conexion() as conn:
            filas = conn.execute(f"{self._PEDIDO} WHERE id = ?", (pedido_id,)).fetchall()
            pedidos = self._armar(conn, filas)
        return pedidos[0] if pedidos else None

    def add(self, pedido: Pedido) -> Pedido:
        """Guarda el pedido y sus lineas en una sola transaccion."""
        with conexion() as conn:
            fila = conn.execute(
                "INSERT INTO pedidos (comprador_id, estado, moneda, zona, subtotal, envio, "
                "total, plataforma, cooperativa, creado_en) "
                "OUTPUT INSERTED.id "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CAST(? AS DATETIMEOFFSET))",
                (
                    pedido.comprador_id,
                    pedido.estado.value,
                    pedido.moneda.value,
                    pedido.zona.value,
                    pedido.subtotal,
                    pedido.envio,
                    pedido.total,
                    pedido.plataforma,
                    pedido.cooperativa,
                    pedido.creado_en.isoformat(),
                ),
            ).fetchone()
            pedido.id = fila["id"]
            conn.executemany(
                "INSERT INTO pedido_items (pedido_id, prenda_id, artesano_id, nombre_prenda, "
                "cantidad, precio_unitario, subtotal) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        pedido.id,
                        i.prenda_id,
                        i.artesano_id,
                        i.nombre_prenda,
                        i.cantidad,
                        i.precio_unitario,
                        i.subtotal,
                    )
                    for i in pedido.items
                ],
            )
        return pedido

    def list_by_comprador(self, comprador_id: int) -> list[Pedido]:
        """Del mas reciente al mas antiguo."""
        with conexion() as conn:
            filas = conn.execute(
                f"{self._PEDIDO} WHERE comprador_id = ? ORDER BY id DESC", (comprador_id,)
            ).fetchall()
            return self._armar(conn, filas)

    def list_items_de_artesano(self, artesano_id: str) -> list[tuple[Pedido, PedidoItem]]:
        """Lineas vendidas de un artesano, junto a su pedido, de la mas reciente a la mas antigua."""
        with conexion() as conn:
            filas = conn.execute(
                f"{self._PEDIDO} WHERE id IN "
                "(SELECT pedido_id FROM pedido_items WHERE artesano_id = ?) ORDER BY id DESC",
                (artesano_id,),
            ).fetchall()
            pedidos = self._armar(conn, filas)
        return [(p, i) for p in pedidos for i in p.items if i.artesano_id == artesano_id]
