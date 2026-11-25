"""Validaciones de texto reutilizables (puras, sin dependencias de FastAPI ni de la base)."""
import base64
import binascii
import re
import unicodedata

from backend.config import MAX_FOTO_BYTES

# ---------------- Correo ----------------
# Errores de tipeo frecuentes -> dominio correcto
DOMINIOS_CORREGIDOS = {
    "gmial.com": "gmail.com",
    "gmai.com": "gmail.com",
    "gamil.com": "gmail.com",
    "gnail.com": "gmail.com",
    "gmail.co": "gmail.com",
    "gmail.con": "gmail.com",
    "gmail.cm": "gmail.com",
    "gmail.om": "gmail.com",
    "hotmial.com": "hotmail.com",
    "hotmal.com": "hotmail.com",
    "hotmail.con": "hotmail.com",
    "outlok.com": "outlook.com",
    "outlook.con": "outlook.com",
    "yaho.com": "yahoo.com",
    "yahoo.con": "yahoo.com",
}

_REGEX_DOMINIO = re.compile(r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,}")
_REGEX_USUARIO = re.compile(r"[A-Za-z0-9._%+-]+")


def validar_correo(valor: str) -> str:
    """Devuelve el mensaje de error, o "" si el correo es válido (misma lógica del frontend)."""
    correo = valor.strip()
    if correo == "":
        return "Escribe tu correo electrónico."

    arrobas = correo.count("@")
    if arrobas == 0:
        return "Falta el símbolo @ (ejemplo: nombre@gmail.com)."
    if arrobas > 1:
        return "El correo solo puede tener un @."

    usuario, dominio = correo.split("@")
    if usuario == "":
        return "Escribe tu usuario antes del @."
    if dominio == "":
        return "Escribe el dominio después del @ (ejemplo: gmail.com)."

    if (
        not _REGEX_USUARIO.fullmatch(usuario)
        or usuario.startswith(".")
        or usuario.endswith(".")
        or ".." in usuario
    ):
        return "El usuario del correo tiene caracteres no válidos."

    dominio_min = dominio.lower()
    sugerido = DOMINIOS_CORREGIDOS.get(dominio_min)
    if sugerido:
        return f"¿Quisiste decir @{sugerido}?"

    if not _REGEX_DOMINIO.fullmatch(dominio_min):
        return "El dominio no es válido. Usa uno como gmail.com, hotmail.com u outlook.com."
    return ""


# ---------------- Fibras ----------------
_REGEX_FIBRA = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:[ -][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*")


def normalizar_fibra(texto: str) -> str:
    """Limpia y da formato uniforme ("vicuña" / "VICUÑA" -> "Vicuña"). Lanza ValueError."""
    limpio = re.sub(r"\s+", " ", texto.strip())
    if len(limpio) < 3:
        raise ValueError("Escribe al menos 3 letras.")
    if len(limpio) > 30:
        raise ValueError("Máximo 30 caracteres.")
    if not _REGEX_FIBRA.fullmatch(limpio):
        raise ValueError("Usa solo letras (sin números ni símbolos).")
    minus = limpio.lower()
    return minus[0].upper() + minus[1:]


def clave_fibra(texto: str) -> str:
    """Clave para detectar duplicados sin importar mayúsculas ni tildes."""
    descompuesto = unicodedata.normalize("NFD", texto)
    sin_tildes = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return sin_tildes.lower()


# ---------------- Fotografía (data URL) ----------------
_REGEX_FOTO = re.compile(r"data:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/]+={0,2})")
MAX_FOTO_CARACTERES = MAX_FOTO_BYTES * 4 // 3 + 128


def _firma_valida(mime: str, datos: bytes) -> bool:
    if mime == "image/jpeg":
        return datos.startswith(b"\xff\xd8\xff")
    if mime == "image/png":
        return datos.startswith(b"\x89PNG\r\n\x1a\n")
    if mime == "image/webp":
        return datos[:4] == b"RIFF" and datos[8:12] == b"WEBP"
    return False


def validar_foto(valor: str) -> str:
    """Comprueba que sea un data URL de JPG/PNG/WebP real y de hasta 2 MB. Lanza ValueError."""
    limite_mb = MAX_FOTO_BYTES // (1024 * 1024)
    if len(valor) > MAX_FOTO_CARACTERES:
        raise ValueError(f"La imagen pesa más de {limite_mb} MB.")
    coincide = _REGEX_FOTO.fullmatch(valor)
    if not coincide:
        raise ValueError("Usa una imagen JPG, PNG o WebP.")
    mime, contenido = coincide.groups()
    try:
        datos = base64.b64decode(contenido, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("No se pudo leer la imagen.") from None
    if len(datos) > MAX_FOTO_BYTES:
        raise ValueError(f"La imagen pesa más de {limite_mb} MB.")
    if not _firma_valida(mime, datos):
        raise ValueError("El archivo no corresponde a una imagen válida.")
    return valor
