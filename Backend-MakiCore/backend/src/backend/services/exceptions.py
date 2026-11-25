# ---------- Autenticación y permisos ----------
class NotAuthenticatedError(Exception):
    """Falta el token, es inválido o la sesión venció."""

    def __init__(self, mensaje: str = "Debes iniciar sesión.") -> None:
        super().__init__(mensaje)


class InvalidCredentialsError(Exception):
    """Correo o contraseña incorrectos."""

    def __init__(self) -> None:
        super().__init__("Correo o contraseña incorrectos.")


class ForbiddenRoleError(Exception):
    """El usuario no tiene el rol que pide la acción."""

    def __init__(self, rol: str) -> None:
        self.rol = rol
        super().__init__(f"Esta acción es solo para usuarios con rol {rol}.")


# ---------- Usuarios ----------
class UsuarioAlreadyExistsError(Exception):
    """Ya hay una cuenta con ese correo."""

    def __init__(self, correo: str) -> None:
        self.correo = correo
        super().__init__("Ya existe una cuenta con ese correo. Inicia sesión.")


# ---------- Fibras ----------
class FibraAlreadyExistsError(Exception):
    """La fibra ya existe (sin importar mayúsculas ni tildes)."""

    def __init__(self, nombre: str) -> None:
        self.nombre = nombre
        super().__init__(f'Esa fibra ya existe: "{nombre}".')


# ---------- Prendas ----------
class PrendaNotFoundError(Exception):
    """No existe una prenda con el id solicitado."""

    def __init__(self, prenda_id: str) -> None:
        self.prenda_id = prenda_id
        super().__init__(f"No existe una prenda con id '{prenda_id}'.")


class PrendaAgotadaError(Exception):
    """La prenda no tiene stock."""

    def __init__(self, nombre: str) -> None:
        self.nombre = nombre
        super().__init__(f"{nombre} está agotada.")


class StockInsuficienteError(Exception):
    """Se pidió más de lo que hay."""

    def __init__(self, nombre: str, disponible: int) -> None:
        self.nombre = nombre
        self.disponible = disponible
        super().__init__(f"No hay stock suficiente de {nombre} (quedan {disponible}).")


class CantidadMaximaError(Exception):
    """Se superó el máximo de unidades por prenda."""

    def __init__(self, nombre: str, maximo: int) -> None:
        self.nombre = nombre
        self.maximo = maximo
        super().__init__(f"Máximo {maximo} unidades de {nombre}.")


# ---------- Pedidos ----------
class PedidoNotFoundError(Exception):
    """No existe un pedido con ese id (o no es del comprador que lo pide)."""

    def __init__(self, pedido_id: int) -> None:
        self.pedido_id = pedido_id
        super().__init__(f"No existe un pedido con id '{pedido_id}'.")
