from pydantic import BaseModel, Field, field_validator

from backend.schemas.enums import Rol
from backend.schemas.usuarios import UsuarioOut
from backend.validators import validar_correo


class RegistroIn(BaseModel):
    correo: str = Field(..., max_length=254, examples=["ana@gmail.com"])
    clave: str = Field(..., min_length=6, max_length=128)  # la contraseña no se recorta
    rol: Rol

    @field_validator("correo")
    @classmethod
    def _correo_valido(cls, valor: str) -> str:
        mensaje = validar_correo(valor)
        if mensaje:
            raise ValueError(mensaje)
        return valor.strip().lower()


class LoginIn(BaseModel):
    correo: str = Field(..., min_length=1, max_length=254, examples=["ana@gmail.com"])
    clave: str = Field(..., min_length=1, max_length=128)

    @field_validator("correo")
    @classmethod
    def _normalizar(cls, valor: str) -> str:
        return valor.strip().lower()


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_en: int  # segundos
    usuario: UsuarioOut
