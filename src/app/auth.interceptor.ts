import { HttpInterceptorFn } from "@angular/common/http";
import { inject } from "@angular/core";
import { API_URL } from "./api.config";
import { SesionToken } from "./sesion-token";

/** Agrega «Authorization: Bearer <token>» a las peticiones hacia nuestro backend (y solo a ellas). */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(SesionToken).token();
  if (token === null || !req.url.startsWith(API_URL)) return next(req);
  return next(req.clone({ setHeaders: { Authorization: "Bearer " + token } }));
};
