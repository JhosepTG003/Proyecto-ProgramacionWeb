from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.config import MAX_PRECIO_USD, MAX_STOCK
from backend.validators import MAX_FOTO_CARACTERES, normalizar_fibra, validar_foto


class PrendaCreate(BaseModel):
    """Datos que envía el artesano. El artesano y el código los pone el servidor."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(..., min_length=1, max_length=100, examples=["Chullo Andino"])
    fibra: str = Field(..., examples=["Alpaca"])
    tinte: str = Field(..., min_length=1, max_length=100, examples=["Nogal (Marrón natural)"])
    precio_centavos_usd: int = Field(..., gt=0, le=MAX_PRECIO_USD * 100, examples=[3500])
    stock: int = Field(..., ge=1, le=MAX_STOCK, examples=[5])
    foto: str | None = Field(
        default=None,
        max_length=MAX_FOTO_CARACTERES,
        description="Data URL JPG/PNG/WebP de hasta 2 MB (opcional).",
    )

    @field_validator("fibra")
    @classmethod
    def _fibra_valida(cls, valor: str) -> str:
        return normalizar_fibra(valor)

    @field_validator("foto")
    @classmethod
    def _foto_valida(cls, valor: str | None) -> str | None:
        if valor is None or valor == "":
            return None
        return validar_foto(valor)


class Prenda(BaseModel):
    """Prenda almacenada. Misma forma que la interfaz Prenda del frontend."""

    id: str  # también es el código del QR (MAKI-0001...)
    nombre: str
    artesano: str  # nombre público, nunca el correo
    artesano_id: str
    fibra: str
    tinte: str
    precio_centavos_usd: int
    stock: int
    foto: str | None = None
