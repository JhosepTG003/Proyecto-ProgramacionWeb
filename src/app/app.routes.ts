import { Routes } from "@angular/router";
import { artesanoGuard } from "./artesano.guard";

export const routes: Routes = [
  { path: "", pathMatch: "full", redirectTo: "catalogo" },
  {
    path: "catalogo",
    title: "Catálogo · Maki Core",
    loadComponent: () => import("./catalogo/catalogo.component").then((m) => m.CatalogoComponent),
  },
  {
    path: "carrito",
    title: "Carrito · Maki Core",
    loadComponent: () => import("./carrito/carrito.component").then((m) => m.CarritoComponent),
  },
  {
    path: "login",
    title: "Ingresar · Maki Core",
    loadComponent: () => import("./login/login.component").then((m) => m.LoginComponent),
  },
  {
    path: "artesano",
    title: "Área del artesano · Maki Core",
    canActivate: [artesanoGuard],
    loadComponent: () => import("./artesano/artesano.component").then((m) => m.ArtesanoComponent),
  },
  { path: "**", redirectTo: "catalogo" },
];
