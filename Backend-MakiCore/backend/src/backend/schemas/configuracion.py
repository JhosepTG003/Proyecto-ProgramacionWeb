from pydantic import BaseModel


class Configuracion(BaseModel):
    """Reglas de negocio que el frontend necesita para validar y mostrar precios."""

    tasa_eur: float
    tarifas_envio_centavos_usd: dict[str, int]
    porcentaje_plataforma: int
    max_cantidad_por_prenda: int
    max_precio_usd: int
    max_stock: int
    tipos_foto: list[str]
    max_foto_bytes: int
