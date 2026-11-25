"""Contraseñas (PBKDF2-SHA256 de la biblioteca estándar) y tokens de sesión."""
import base64
import hashlib
import hmac
import os
import secrets
from functools import lru_cache

_ITERACIONES = 600_000


def _b64(datos: bytes) -> str:
    return base64.b64encode(datos).decode("ascii")


def hash_clave(clave: str) -> str:
    sal = os.urandom(16)
    derivada = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), sal, _ITERACIONES)
    return f"pbkdf2_sha256${_ITERACIONES}${_b64(sal)}${_b64(derivada)}"


def verificar_clave(clave: str, almacenado: str) -> bool:
    try:
        algoritmo, iteraciones, sal, esperado = almacenado.split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        derivada = hashlib.pbkdf2_hmac(
            "sha256", clave.encode("utf-8"), base64.b64decode(sal), int(iteraciones)
        )
        return hmac.compare_digest(derivada, base64.b64decode(esperado))
    except (ValueError, TypeError):
        return False


@lru_cache
def hash_falso() -> str:
    """Se verifica contra este hash cuando el correo no existe, para no revelar por tiempo
    de respuesta qué correos están registrados."""
    return hash_clave("clave-que-nadie-usa")


def generar_token() -> str:
    """Token de sesión aleatorio e impredecible."""
    return secrets.token_urlsafe(32)
