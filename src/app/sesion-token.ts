import { Injectable, signal } from "@angular/core";

const CLAVE = "maki.token";

/**
 * Guarda el token de sesión que entrega el backend. Vive en sessionStorage (se conserva al
 * recargar la pestaña y se borra al cerrarla). Está separado de TiendaService a propósito:
 * el interceptor HTTP lo lee, y si dependiera de TiendaService habría una dependencia circular.
 */
@Injectable({ providedIn: "root" })
export class SesionToken {
  readonly token = signal<string | null>(this.leer());

  guardar(valor: string) {
    this.token.set(valor);
    try {
      sessionStorage.setItem(CLAVE, valor);
    } catch {
      /* sin almacenamiento disponible: la sesión dura hasta recargar */
    }
  }

  borrar() {
    this.token.set(null);
    try {
      sessionStorage.removeItem(CLAVE);
    } catch {
      /* nada que borrar */
    }
  }

  private leer(): string | null {
    try {
      return sessionStorage.getItem(CLAVE);
    } catch {
      return null;
    }
  }
}
