import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { AppComponent } from '../app.component';
import { routes } from '../app.routes';
import { TiendaService } from '../tienda.service';

describe('Catálogo dinámico', () => {
  it('muestra la prenda nueva cuando un artesano la registra', async () => {
    TestBed.configureTestingModule({ providers: [provideRouter(routes)] });
    const router = TestBed.inject(Router);
    const tienda = TestBed.inject(TiendaService);
    const fixture = TestBed.createComponent(AppComponent);
    const el = fixture.nativeElement as HTMLElement;

    const ir = async (url: string) => {
      await router.navigateByUrl(url);
      await fixture.whenStable();
    };

    await ir('/catalogo');
    await vi.waitFor(() => expect(el.querySelectorAll('app-catalogo .card').length).toBe(2));

    // Al entrar como artesano, la app lo lleva sola a su área.
    tienda.iniciarSesion('artesano@maki.pe', 'artesano');
    await vi.waitFor(() => expect(el.querySelector('app-artesano')).not.toBeNull());
    expect(router.url).toBe('/artesano');

    const escribir = async (selector: string, valor: string) => {
      const campo = el.querySelector(`app-artesano ${selector}`) as HTMLInputElement;
      campo.value = valor;
      campo.dispatchEvent(new Event('input'));
      campo.dispatchEvent(new Event('change'));
      await fixture.whenStable();
    };
    await escribir('input[placeholder^="Ej: Chalina"]', 'Manta Huancaína');
    await escribir('input[placeholder^="Ej: Cochinilla"]', 'Molle');
    await escribir('select', 'Llama');
    await escribir('input[type=number]', '80');

    (el.querySelector('app-artesano button.btn-lg') as HTMLButtonElement).click();
    await fixture.whenStable();

    await ir('/catalogo');
    await vi.waitFor(() => expect(el.querySelectorAll('app-catalogo .card').length).toBe(3));
    const catalogo = el.querySelector('app-catalogo')!;
    expect(catalogo.textContent).toContain('Manta Huancaína');
    expect(catalogo.textContent).toContain('Llama');
    expect(tienda.ultimoQR()).toBe('MAKI-0001');

    // El catálogo es público: muestra el nombre del artesano, nunca su correo.
    expect(catalogo.textContent).toContain('Artesano ART-0003');
    expect(catalogo.textContent).not.toContain('artesano@maki.pe');

    // la prenda nueva se puede comprar y se convierte de moneda
    tienda.agregar('MAKI-0001');
    tienda.cambiarMoneda('EUR');
    expect(tienda.subtotal()).toBe(7360); // 80 USD x 0.92 = 73.60 EUR, en centavos
    expect(el.querySelector('nav')!.textContent).toContain('Maki Core');
  });
});
