import { Component, inject } from "@angular/core";
import { FormField } from "@angular/forms/signals";
import { TiendaService } from "../tienda.service";

@Component({
  selector: "app-carrito",
  standalone: true,
  imports: [FormField],
  templateUrl: "./carrito.component.html",
})
export class CarritoComponent {
  tienda = inject(TiendaService);
}
