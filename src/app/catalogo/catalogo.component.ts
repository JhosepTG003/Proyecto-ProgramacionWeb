import { Component, computed, inject, signal } from "@angular/core";
import { TiendaService } from "../tienda.service";

// Colores andinos para la cabecera de cada tarjeta (según la fibra)
const PALETA = ["#9c2f2f", "#b5651d", "#2f6f6a", "#5b3a6e", "#3d5a80", "#7a5c2e"];

@Component({
  selector: "app-catalogo",
  standalone: true,
  templateUrl: "./catalogo.component.html",
})
export class CatalogoComponent {
  tienda = inject(TiendaService);

  filtro = signal("Todas");

  // Botones de filtro: "Todas" + todas las fibras registradas (incluye las nuevas aunque aún no tengan prendas).
  fibras = computed(() => ["Todas", ...this.tienda.fibras()]);

  prendasFiltradas = computed(() => {
    const f = this.filtro();
    return f === "Todas"
      ? this.tienda.prendas()
      : this.tienda.prendas().filter((p) => p.fibra === f);
  });

  cambiarFiltro(fibra: string) {
    this.filtro.set(fibra);
  }

  contar(fibra: string): number {
    return fibra === "Todas"
      ? this.tienda.prendas().length
      : this.tienda.prendas().filter((p) => p.fibra === fibra).length;
  }

  colorFibra(fibra: string): string {
    let h = 0;
    for (const ch of fibra) h = (h * 31 + ch.charCodeAt(0)) % 997;
    return PALETA[h % PALETA.length];
  }
}
