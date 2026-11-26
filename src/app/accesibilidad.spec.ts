import { TestBed } from '@angular/core/testing';
import { CarritoComponent } from './carrito/carrito.component';
import { ArtesanoComponent } from './artesano/artesano.component';
import { LoginComponent } from './login/login.component';
import { TiendaService } from './tienda.service';

// Cada <label for="x"> debe apuntar a un campo con id="x" (así los lectores de pantalla
// y el clic en la etiqueta funcionan), y todo campo de formulario debe tener etiqueta.
describe('Accesibilidad de formularios', () => {
  const casos = [
    { nombre: 'login', tipo: LoginComponent },
    { nombre: 'artesano', tipo: ArtesanoComponent },
    { nombre: 'carrito', tipo: CarritoComponent },
  ];

  for (const { nombre, tipo } of casos) {
    it(`las etiquetas de ${nombre} están asociadas a sus campos`, async () => {
      TestBed.inject(TiendaService).iniciarSesion('ana@gmail.com', 'artesano');
      const fixture = TestBed.createComponent(tipo);
      const el = fixture.nativeElement as HTMLElement;
      // Muestra también el panel de "nueva fibra" en el formulario del artesano
      const comp = fixture.componentInstance as { agregandoFibra?: { set(v: boolean): void } };
      comp.agregandoFibra?.set(true);
      TestBed.inject(TiendaService).agregar('poncho-andino', false);
      await fixture.whenStable();

      const etiquetas = Array.from(el.querySelectorAll('label'));
      for (const e of etiquetas) {
        const destino = e.getAttribute('for');
        expect(destino, 'label sin for: ' + e.textContent).toBeTruthy();
        expect(el.querySelector('#' + destino), 'no existe #' + destino).not.toBeNull();
      }

      const campos = Array.from(el.querySelectorAll('input, select, textarea'));
      for (const c of campos) {
        const id = c.getAttribute('id');
        const tieneEtiqueta = !!id && !!el.querySelector(`label[for="${id}"]`);
        expect(tieneEtiqueta, 'campo sin etiqueta: ' + (id ?? c.outerHTML.slice(0, 60))).toBe(true);
      }
    });
  }
});
