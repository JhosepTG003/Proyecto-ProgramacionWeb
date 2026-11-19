import { Component, signal, inject } from "@angular/core";
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

  ir(nombre: string) {
    this.pagina.set(nombre);
  }
}
