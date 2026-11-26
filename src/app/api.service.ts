import { HttpClient, HttpErrorResponse } from "@angular/common/http";
import { Injectable, Injector, inject } from "@angular/core";
import { firstValueFrom } from "rxjs";
import { API_URL } from "./api.config";
import type { Moneda, Prenda, Rol, Zona } from "./tienda.service";

// ---------- Formas que devuelve / recibe el backend (snake_case) ----------
export interface UsuarioApi {
  id: number;
  correo: string;
  rol: Rol;
  artesano_id: string | null;
  nombre_publico: string | null;
}

export interface TokenApi {
  access_token: string;
  token_type: string;
  expira_en: number;
  usuario: UsuarioApi;
}

interface PrendaApi {
  id: string;
  nombre: string;
  artesano: string;
  artesano_id: string;
  fibra: string;
  tinte: string;
  precio_centavos_usd: number;
  stock: number;
  foto: string | null;
}

export interface NuevaPrendaApi {
  nombre: string;
  fibra: string;
  tinte: string;
  precio_centavos_usd: number;
  stock: number;
  foto: string | null;
}

export interface PedidoEntrada {
  items: { prenda_id: string; cantidad: number }[];
  moneda: Moneda;
  zona: Zona;
}

export interface PedidoApi {
  id: number;
  estado: string;
  total: number;
  mensaje: string | null;
}

// El backend usa snake_case y el frontend camelCase: se traduce aquí, en un solo lugar.
function aPrenda(p: PrendaApi): Prenda {
  return {
    id: p.id,
    nombre: p.nombre,
    artesano: p.artesano,
    artesanoId: p.artesano_id,
    fibra: p.fibra,
    tinte: p.tinte,
    precioCentavosUSD: p.precio_centavos_usd,
    stock: p.stock,
    foto: p.foto ?? undefined,
  };
}

/** Convierte cualquier error de la API en un texto para mostrar al usuario. */
export function mensajeError(e: unknown): string {
  if (e instanceof HttpErrorResponse) {
    if (e.status === 0) return "No se pudo conectar con el servidor. ¿Está encendido el backend?";
    const detalle = e.error?.detail;
    if (typeof detalle === "string") return detalle;
    if (Array.isArray(detalle) && detalle.length > 0) {
      // Errores de validación de FastAPI: [{ msg: "Value error, <mensaje>" }]
      const msg = String(detalle[0]?.msg ?? "").replace(/^Value error, /, "");
      return msg || "Los datos enviados no son válidos.";
    }
    return "El servidor respondió con un error (" + e.status + ").";
  }
  return "Ocurrió un error inesperado.";
}

@Injectable({ providedIn: "root" })
export class ApiService {
  private injector = inject(Injector);

  // HttpClient se pide recién al hacer la primera petición, no al crear el servicio.
  private get http(): HttpClient {
    return this.injector.get(HttpClient);
  }

  // ---------- Auth ----------
  login(correo: string, clave: string): Promise<TokenApi> {
    return firstValueFrom(this.http.post<TokenApi>(API_URL + "/auth/login", { correo, clave }));
  }

  registro(correo: string, clave: string, rol: Rol): Promise<TokenApi> {
    return firstValueFrom(
      this.http.post<TokenApi>(API_URL + "/auth/registro", { correo, clave, rol }),
    );
  }

  me(): Promise<UsuarioApi> {
    return firstValueFrom(this.http.get<UsuarioApi>(API_URL + "/auth/me"));
  }

  async logout(token: string): Promise<void> {
    await firstValueFrom(
      this.http.post<void>(API_URL + "/auth/logout", {}, { headers: { Authorization: "Bearer " + token } }),
    );
  }

  // ---------- Catálogo ----------
  async prendas(): Promise<Prenda[]> {
    const lista = await firstValueFrom(this.http.get<PrendaApi[]>(API_URL + "/prendas"));
    return lista.map(aPrenda);
  }

  async crearPrenda(datos: NuevaPrendaApi): Promise<Prenda> {
    return aPrenda(await firstValueFrom(this.http.post<PrendaApi>(API_URL + "/prendas", datos)));
  }

  // ---------- Fibras ----------
  async fibras(): Promise<string[]> {
    const lista = await firstValueFrom(
      this.http.get<{ id: number; nombre: string }[]>(API_URL + "/fibras"),
    );
    return lista.map((f) => f.nombre);
  }

  async crearFibra(nombre: string): Promise<string> {
    const fibra = await firstValueFrom(
      this.http.post<{ id: number; nombre: string }>(API_URL + "/fibras", { nombre }),
    );
    return fibra.nombre;
  }

  // ---------- Pedidos ----------
  pagar(pedido: PedidoEntrada): Promise<PedidoApi> {
    return firstValueFrom(this.http.post<PedidoApi>(API_URL + "/pedidos", pedido));
  }
}
