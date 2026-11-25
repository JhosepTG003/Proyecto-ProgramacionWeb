from enum import Enum


class Rol(str, Enum):
    COMPRADOR = "comprador"
    ARTESANO = "artesano"


class Moneda(str, Enum):
    USD = "USD"
    EUR = "EUR"


class Zona(str, Enum):
    AMERICA = "America"
    EUROPA = "Europa"
    OTROS = "Otros"


class EstadoPedido(str, Enum):
    APROBADO = "Aprobado"
