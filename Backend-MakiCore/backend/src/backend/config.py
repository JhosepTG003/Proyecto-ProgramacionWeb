"""Reglas de negocio y configuración en un solo lugar (equivale a configuracion.ts del frontend).

Todos los montos van en CENTAVOS enteros para evitar errores de redondeo con decimales.
Los valores de entorno son opcionales: sin ellos el servidor funciona con los de abajo.
"""
import os
from decimal import Decimal

from backend.schemas.enums import Zona

# ---------- Reglas de negocio ----------
# Tasa de conversión USD -> EUR (fija en este prototipo; podría venir de un servicio externo).
TASA_EUR = Decimal("0.92")

# Tarifa fija de envío por zona, en centavos de USD.
TARIFAS_ENVIO_CENTAVOS_USD: dict[Zona, int] = {
    Zona.AMERICA: 2500,
    Zona.EUROPA: 3000,
    Zona.OTROS: 4000,
}

# Parte de cada venta que se queda la plataforma (RF021); el resto va a la cooperativa.
PORCENTAJE_PLATAFORMA = 20

# Máximo de unidades de una misma prenda por pedido.
MAX_CANTIDAD_POR_PRENDA = 10

# Precio base máximo que puede registrar un artesano (USD) y stock máximo por prenda.
MAX_PRECIO_USD = 10_000
MAX_STOCK = 9_999

# Fotografía de la prenda: formatos admitidos y tamaño máximo.
TIPOS_FOTO = ("image/jpeg", "image/png", "image/webp")
MAX_FOTO_BYTES = 2 * 1024 * 1024  # 2 MB

MENSAJE_PAGO_APROBADO = (
    "Pago aprobado. Se notificó la venta al artesano y se ordenó la transferencia "
    "del 80 % a la cooperativa."
)

# ---------- Entorno ----------
# Orígenes permitidos por CORS, separados por coma (el frontend Angular corre en el 4200).
CORS_ORIGINS = [
    origen.strip()
    for origen in os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")
    if origen.strip()
]

# Cadena de conexión ODBC a SQL Server, p. ej.
# DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\SQLEXPRESS;DATABASE=maki;Trusted_Connection=yes;TrustServerCertificate=yes;
# Si está vacía, el servidor usa el almacenamiento en memoria (se pierde al reiniciar).
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# Minutos que dura una sesión iniciada.
SESION_MINUTOS = int(os.getenv("SESION_MINUTOS", "60"))

# Carga artesanos, fibras y prendas de ejemplo al arrancar (la memoria empieza vacía).
SEED_DEMO_DATA = os.getenv("SEED_DEMO_DATA", "true").lower() != "false"
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "maki123")
