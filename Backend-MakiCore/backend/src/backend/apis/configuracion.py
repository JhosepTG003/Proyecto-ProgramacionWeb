from fastapi import APIRouter

from backend import config
from backend.schemas.configuracion import Configuracion

router = APIRouter(prefix="/configuracion", tags=["configuracion"])


@router.get("", response_model=Configuracion, summary="Reglas de negocio")
def obtener_configuracion() -> Configuracion:
    """Una sola fuente de verdad para tasas, tarifas y límites (el frontend ya no los duplica)."""
    return Configuracion(
        tasa_eur=float(config.TASA_EUR),
        tarifas_envio_centavos_usd={
            zona.value: tarifa for zona, tarifa in config.TARIFAS_ENVIO_CENTAVOS_USD.items()
        },
        porcentaje_plataforma=config.PORCENTAJE_PLATAFORMA,
        max_cantidad_por_prenda=config.MAX_CANTIDAD_POR_PRENDA,
        max_precio_usd=config.MAX_PRECIO_USD,
        max_stock=config.MAX_STOCK,
        tipos_foto=list(config.TIPOS_FOTO),
        max_foto_bytes=config.MAX_FOTO_BYTES,
    )
