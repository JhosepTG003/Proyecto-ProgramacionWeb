"""Funciones de dinero en centavos enteros (equivalen a dinero.ts del frontend).

Se usa Decimal y redondeo "mitad hacia arriba" para dar exactamente los mismos resultados
que Math.round de JavaScript (round() de Python redondea mitades al par).
"""
from decimal import ROUND_HALF_UP, Decimal

from backend.config import PORCENTAJE_PLATAFORMA, TARIFAS_ENVIO_CENTAVOS_USD, TASA_EUR
from backend.schemas.enums import Moneda, Zona


def _redondear(valor: Decimal) -> int:
    return int(valor.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def convertir(centavos_usd: int, moneda: Moneda) -> int:
    """Convierte centavos de USD a la moneda indicada, redondeando al centavo más cercano."""
    if moneda == Moneda.EUR:
        return _redondear(Decimal(centavos_usd) * TASA_EUR)
    return centavos_usd


def dividir_venta(
    monto_centavos: int, porcentaje_plataforma: int = PORCENTAJE_PLATAFORMA
) -> tuple[int, int]:
    """Reparte una venta entre (plataforma, cooperativa). Siempre suman el monto original."""
    plataforma = _redondear(Decimal(monto_centavos * porcentaje_plataforma) / Decimal(100))
    return plataforma, monto_centavos - plataforma


def costo_envio(subtotal_centavos: int, zona: Zona, moneda: Moneda) -> int:
    """Envío fijo por zona (tarifa en USD convertida a la moneda); 0 si no hay productos."""
    if subtotal_centavos == 0:
        return 0
    return convertir(TARIFAS_ENVIO_CENTAVOS_USD[zona], moneda)
