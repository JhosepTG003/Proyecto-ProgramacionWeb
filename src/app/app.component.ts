import { Component, signal, inject, effect, untracked } from "@angular/core";
import { TiendaService } from "./tienda.service";
import { LoginComponent } from "./login/login.component";
import { CatalogoComponent } from "./catalogo/catalogo.component";
import { CarritoComponent } from "./carrito/carrito.component";
import { ArtesanoComponent } from "./artesano/artesano.component";

@Component({
  selector: "app-root",
  standalone: true,
  imports: [
    LoginComponent,
    CatalogoComponent,
    CarritoComponent,
    ArtesanoComponent,
  ],
  templateUrl: "./app.component.html",
})
export class AppComponent {
  tienda = inject(TiendaService);
  pagina = signal("catalogo");

  constructor() {
    // Reacciona a los cambios de sesión (rol):
    //  - entra un artesano  -> lo lleva a su área
    //  - entra un comprador -> lo lleva al catálogo
    //  - cierra sesión estando en "Artesano" -> vuelve al catálogo
    effect(() => {
      const rol = this.tienda.rol();
      untracked(() => {
        if (rol === "artesano") this.pagina.set("artesano");
        else if (rol === "comprador") this.pagina.set("catalogo");
        else if (this.pagina() === "artesano") this.pagina.set("catalogo");
      });
    });
  }

  ir(nombre: string) {
    this.pagina.set(nombre);
  }
}
