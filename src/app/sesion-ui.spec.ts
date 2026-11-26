import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { AppComponent } from './app.component';
import { routes } from './app.routes';
import { TiendaService } from './tienda.service';

describe('Sesión en el menú y en /login', () => {
  async function montar() {
    TestBed.configureTestingModule({ providers: [provideRouter(routes)] });
    const router = TestBed.inject(Router);
    const tienda = TestBed.inject(TiendaService);
    const fixture = TestBed.createComponent(AppComponent);
    await router.navigateByUrl('/catalogo');
    await fixture.whenStable();
    return { router, tienda, fixture, el: fixture.nativeElement as HTMLElement };
  }
  const botonesNav = (el: HTMLElement) => Array.from(el.querySelectorAll('nav button, nav a')).map((b) => b.textContent!.trim());

  it('sin sesión el menú ofrece "Ingresar" y no "Cerrar sesión"', async () => {
    const { el } = await montar();
    const textos = botonesNav(el);
    expect(textos.some((t) => t.includes('Ingresar'))).toBe(true);
    expect(textos.some((t) => t.includes('Cerrar sesión'))).toBe(false);
  });

  it('con sesión el menú cambia "Ingresar" por "Cerrar sesión", que funciona', async () => {
    const { el, tienda, router } = await montar();
    tienda.iniciarSesion('ana@gmail.com', 'comprador');
    await vi.waitFor(() => expect(botonesNav(el).some((t) => t.includes('Cerrar sesión'))).toBe(true));
    expect(botonesNav(el).some((t) => t.includes('Ingresar'))).toBe(false);

    const salir = Array.from(el.querySelectorAll('nav button')).find((b) => b.textContent!.includes('Cerrar sesión')) as HTMLButtonElement;
    salir.click();
    await vi.waitFor(() => expect(tienda.estaLogueado()).toBe(false));
    await vi.waitFor(() => expect(botonesNav(el).some((t) => t.includes('Ingresar'))).toBe(true));
    expect(router.url).toBe('/catalogo');
  });

  it('con sesión, /login no deja cambiar de rol: solo ofrece cerrar sesión', async () => {
    const { el, tienda, router, fixture } = await montar();
    await router.navigateByUrl('/carrito'); // para que la redirección al catálogo se note
    tienda.iniciarSesion('ana@gmail.com', 'comprador');
    // Al iniciar sesión la app lleva al comprador al catálogo; luego él mismo visita /login.
    await vi.waitFor(() => expect(router.url).toBe('/catalogo'));
    await router.navigateByUrl('/login');
    await fixture.whenStable();
    await vi.waitFor(() => expect(el.querySelector('app-login')).not.toBeNull());
    const login = el.querySelector('app-login')!;
    await vi.waitFor(() => expect(login.textContent).toContain('Ya iniciaste sesión como'));
    expect(login.textContent).not.toContain('Artesano');
    expect(login.querySelector('input')).toBeNull();

    (login.querySelector('button.btn-outline-danger') as HTMLButtonElement).click();
    await vi.waitFor(() => expect(login.querySelector('input#login-correo')).not.toBeNull());
    expect(tienda.estaLogueado()).toBe(false);
  });
});
