import { inject } from "@angular/core";
import { CanActivateFn, Router } from "@angular/router";
import { TiendaService } from "./tienda.service";

// Solo deja entrar a /artesano si hay sesión de artesano; si no, manda a /login.
// (Con backend, esta decisión debe respaldarla el servidor: el guard solo mejora la experiencia.)
export const artesanoGuard: CanActivateFn = () => {
  const tienda = inject(TiendaService);
  const router = inject(Router);
  return tienda.rol() === "artesano" ? true : router.createUrlTree(["/login"]);
};
