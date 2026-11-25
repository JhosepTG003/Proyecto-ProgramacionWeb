"""Datos de ejemplo: los mismos artesanos, fibras y prendas que traía el frontend.

La memoria empieza vacía en cada arranque, así que se cargan al iniciar el servidor.
"""
from backend import config
from backend.repositories.fibras import fibra_repository
from backend.repositories.prendas import prenda_repository
from backend.repositories.usuarios import usuario_repository
from backend.schemas.enums import Rol
from backend.schemas.prendas import Prenda
from backend.schemas.usuarios import Usuario
from backend.security import hash_clave


def sembrar_datos_demo() -> None:
    """Solo actúa si no hay usuarios, así que es seguro llamarla más de una vez."""
    if usuario_repository.list():
        return

    clave_hash = hash_clave(config.DEMO_PASSWORD)  # un solo hash para los tres usuarios
    usuario_repository.add(
        Usuario(
            correo="taller.godino@maki.pe", clave_hash=clave_hash, rol=Rol.ARTESANO,
            artesano_id="ART-0001", nombre_publico="Taller Godiño Yanqui",
        )
    )
    usuario_repository.add(
        Usuario(
            correo="taller.palacios@maki.pe", clave_hash=clave_hash, rol=Rol.ARTESANO,
            artesano_id="ART-0002", nombre_publico="Taller Palacios Yalico",
        )
    )
    usuario_repository.add(
        Usuario(correo="comprador@maki.pe", clave_hash=clave_hash, rol=Rol.COMPRADOR)
    )

    for nombre in ("Alpaca", "Llama", "Lana ovina"):
        fibra_repository.add(nombre)

    prenda_repository.add(
        Prenda(
            id="poncho-andino", nombre="Poncho Andino Tradicional",
            artesano="Taller Godiño Yanqui", artesano_id="ART-0001", fibra="Alpaca",
            tinte="Nogal (Marrón natural)", precio_centavos_usd=15000, stock=12,
        )
    )
    prenda_repository.add(
        Prenda(
            id="chalina-hualhuas", nombre="Chalina Hualhuas",
            artesano="Taller Palacios Yalico", artesano_id="ART-0002", fibra="Lana ovina",
            tinte="Cochinilla (Rojo carmín)", precio_centavos_usd=4500, stock=20,
        )
    )
