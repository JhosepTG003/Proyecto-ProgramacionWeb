from pydantic import BaseModel, ConfigDict

from backend.schemas.enums import Rol


class Usuario(BaseModel):
    """Usuario almacenado. Incluye el hash de la clave, por eso NUNCA se devuelve tal cual."""

    id: int = 0  # lo asigna el repositorio
    correo: str
    clave_hash: str
    rol: Rol
    # Solo los artesanos tienen ID público (ART-0001...) y nombre público.
    # El correo es un dato privado y nunca se expone en el catálogo.
    artesano_id: str | None = None
    nombre_publico: str | None = None


class UsuarioOut(BaseModel):
    """Datos del propio usuario (sin la clave)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    correo: str
    rol: Rol
    artesano_id: str | None = None
    nombre_publico: str | None = None
