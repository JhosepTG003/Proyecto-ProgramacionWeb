import type { Zona } from "./tienda.service";

// Valores de negocio en un solo lugar. Los montos van en CENTAVOS de USD (enteros) para evitar
// errores de redondeo de los decimales de JavaScript (0.1 + 0.2 !== 0.3).

/** Tasa de conversión USD -> EUR (fija en este prototipo; con backend vendría de un servicio). */
export const TASA_EUR = 0.92;

/** Tarifa fija de envío por zona, en centavos de USD. */
export const TARIFAS_ENVIO_CENTAVOS_USD: Record<Zona, number> = {
  America: 2500,
  Europa: 3000,
  Otros: 4000,
};

/** Parte de cada venta que se queda la plataforma (RF021); el resto va a la cooperativa. */
export const PORCENTAJE_PLATAFORMA = 20;

/** Máximo de unidades de una misma prenda en el carrito. */
export const MAX_CANTIDAD_POR_PRENDA = 10;

/** Precio base máximo que puede registrar un artesano, en USD. */
export const MAX_PRECIO_USD = 10000;

/** Stock máximo que puede registrar un artesano por prenda. */
export const MAX_STOCK = 9999;

/** Fotografía de la prenda: formatos admitidos y tamaño máximo. */
export const TIPOS_FOTO = ["image/jpeg", "image/png", "image/webp"] as const;
export const MAX_FOTO_BYTES = 2 * 1024 * 1024; // 2 MB
