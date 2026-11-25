from pydantic import BaseModel, Field, field_validator

from backend.validators import normalizar_fibra


class FibraCreate(BaseModel):
    """Datos necesarios para crear una fibra."""

    nombre: str = Field(..., examples=["Vicuña"])

    @field_validator("nombre")
    @classmethod
    def _nombre_valido(cls, valor: str) -> str:
        return normalizar_fibra(valor)  # lanza ValueError con el mensaje para el usuario


class Fibra(BaseModel):
    """Representación de una fibra almacenada."""

    id: int = 0  # lo asigna el repositorio
    nombre: str
