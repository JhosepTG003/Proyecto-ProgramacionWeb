import { PORCENTAJE_PLATAFORMA, TASA_EUR } from "./configuracion";
import type { Moneda } from "./tienda.service";

/** Convierte un monto en USD (con decimales, como lo escribe el usuario) a centavos enteros. */
export function usdACentavos(usd: number): number {
  return Math.round(usd * 100);
}

/** Convierte centavos de USD a la moneda indicada, redondeando al centavo más cercano. */
export function convertir(centavosUSD: number, moneda: Moneda): number {
  return moneda === "EUR" ? Math.round(centavosUSD * TASA_EUR) : centavosUSD;
}

/** Divide una venta entre plataforma y cooperativa. Siempre suman exactamente el monto original. */
export function dividirVenta(
  montoCentavos: number,
  porcentajePlataforma: number = PORCENTAJE_PLATAFORMA,
): { plataforma: number; cooperativa: number } {
  const plataforma = Math.round((montoCentavos * porcentajePlataforma) / 100);
  return { plataforma, cooperativa: montoCentavos - plataforma };
}
