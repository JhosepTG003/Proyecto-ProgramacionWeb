import { Component, inject, effect, untracked } from "@angular/core";
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from "@angular/router";
import { TiendaService } from "./tienda.service";

@Component({
  selector: "app-root",
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: "./app.component.html",
})
export class AppComponent {
  tienda = inject(TiendaService);
  private router = inject(Router);

  salir() {
    this.tienda.cerrarSesion();
  }

  constructor() {
    // Recupera la sesión guardada y trae el catálogo del backend.
    void this.tienda.iniciarApp();

    // Reacciona a los cambios de sesión (rol):
    //  - entra un artesano  -> lo lleva a su área
    //  - entra un comprador -> lo lleva al catálogo
    //  - cierra sesión estando en el área del artesano -> vuelve al catálogo
    effect(() => {
      const rol = this.tienda.rol();
      untracked(() => {
        if (rol === "artesano") this.router.navigateByUrl("/artesano");
        else if (rol === "comprador") this.router.navigateByUrl("/catalogo");
        else if (this.router.url.startsWith("/artesano")) this.router.navigateByUrl("/catalogo");
      });
    });
  }
}
