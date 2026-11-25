import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { AppComponent } from './app.component';
import { routes } from './app.routes';
import { TiendaService } from './tienda.service';

describe('Navegación', () => {
  async function montar() {
    TestBed.configureTestingModule({ providers: [provideRouter(routes)] });
    const router = TestBed.inject(Router);
    const tienda = TestBed.inject(TiendaService);
    const fixture = TestBed.createComponent(AppComponent);
    await router.navigateByUrl('/');
    await fixture.whenStable();
    return { router, tienda, fixture };
  }

  it('la raíz y las rutas desconocidas llevan al catálogo', async () => {
    const { router } = await montar();
    expect(router.url).toBe('/catalogo');
    await router.navigateByUrl('/no-existe');
    expect(router.url).toBe('/catalogo');
  });

  it('un comprador entra al catálogo y un artesano a su área', async () => {
    const { router, tienda } = await montar();
    tienda.iniciarSesion('ana@gmail.com', 'comprador');
    await vi.waitFor(() => expect(router.url).toBe('/catalogo'));

    tienda.cerrarSesion();
    tienda.iniciarSesion('luis@gmail.com', 'artesano');
    await vi.waitFor(() => expect(router.url).toBe('/artesano'));
  });

  it('al cerrar sesión desde el área del artesano vuelve al catálogo', async () => {
    const { router, tienda } = await montar();
    tienda.iniciarSesion('luis@gmail.com', 'artesano');
    await vi.waitFor(() => expect(router.url).toBe('/artesano'));

    tienda.cerrarSesion();
    await vi.waitFor(() => expect(router.url).toBe('/catalogo'));
  });

  it('el enlace "Artesano" solo aparece con sesión de artesano', async () => {
    const { tienda, fixture } = await montar();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('a[href="/artesano"]')).toBeNull();
    tienda.iniciarSesion('luis@gmail.com', 'artesano');
    await vi.waitFor(() => expect(el.querySelector('a[href="/artesano"]')).not.toBeNull());
  });
});
