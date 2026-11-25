import { TestBed } from '@angular/core/testing';
import { CarritoComponent } from './carrito/carrito.component';
import { TiendaService } from './tienda.service';

describe('Pantalla del carrito', () => {
  function montar() {
    const tienda = TestBed.inject(TiendaService);
    const fixture = TestBed.createComponent(CarritoComponent);
    return { tienda, fixture, el: fixture.nativeElement as HTMLElement };
  }
  const mas = (el: HTMLElement) => el.querySelector('button[aria-label^="Añadir"]') as HTMLButtonElement;

  it('el botón "+" suma sin mostrar el aviso "se añadió"', async () => {
    const { tienda, fixture, el } = montar();
    tienda.agregar('poncho-andino', false);
    await fixture.whenStable();
    mas(el).click();
    await fixture.whenStable();
    expect(tienda.enCarrito('poncho-andino')).toBe(2);
    expect(tienda.aviso()).toBe('');
  });

  it('el botón "+" se desactiva al llegar al máximo', async () => {
    const { tienda, fixture, el } = montar();
    for (let i = 0; i < tienda.maxPorPrenda; i++) tienda.agregar('poncho-andino', false);
    await fixture.whenStable();
    expect(mas(el).disabled).toBe(true);
  });

  it('muestra los montos con el símbolo y 2 decimales', async () => {
    const { tienda, fixture, el } = montar();
    tienda.agregar('chalina-hualhuas', false);
    tienda.cambiarMoneda('EUR');
    await fixture.whenStable();
    expect(el.textContent).toContain('€41.40'); // 45 x 0.92
  });
});
