import { TestBed } from '@angular/core/testing';
import { AppComponent } from '../app.component';
import { TiendaService } from '../tienda.service';

describe('Catálogo dinámico', () => {
  it('muestra la prenda nueva cuando un artesano la registra', async () => {
    const fixture = TestBed.createComponent(AppComponent);
    await fixture.whenStable();
    const el = fixture.nativeElement as HTMLElement;
    const tienda = TestBed.inject(TiendaService);

    expect(el.querySelectorAll('app-catalogo .card').length).toBe(2);

    tienda.iniciarSesion('artesano@maki.pe', 'artesano');
    const set = async (sel: string, v: string) => {
      const i = el.querySelector(`app-artesano ${sel}`) as HTMLInputElement;
      i.value = v;
      i.dispatchEvent(new Event('input'));
      i.dispatchEvent(new Event('change'));
      await fixture.whenStable();
    };
    const inputs = el.querySelectorAll('app-artesano input[type=text]');
    await set('input[type=text]', 'Manta Huancaína');
    (inputs[1] as HTMLInputElement).value = 'Molle';
    inputs[1].dispatchEvent(new Event('input'));
    await set('select', 'Llama');
    await set('input[type=number]', '80');

    (el.querySelector('app-artesano .btn-success') as HTMLButtonElement).click();
    await fixture.whenStable();

    expect(el.querySelectorAll('app-catalogo .card').length).toBe(3);
    expect(el.querySelector('app-catalogo')!.textContent).toContain('Manta Huancaína');
    expect(el.querySelector('app-catalogo')!.textContent).toContain('Llama');
    expect(tienda.ultimoQR()).toBe('MAKI-0001');

    // la prenda nueva se puede comprar y se convierte de moneda
    tienda.agregar('MAKI-0001');
    tienda.cambiarMoneda('EUR');
    expect(tienda.subtotal()).toBeCloseTo(73.6, 2);
    expect(el.querySelector('nav')!.textContent).toContain('Maki Core');
  });
});
