import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { routes } from './app.routes';
import { TiendaService } from './tienda.service';

describe('artesanoGuard', () => {
  beforeEach(() => TestBed.configureTestingModule({ providers: [provideRouter(routes)] }));

  it('sin sesión, /artesano redirige a /login', async () => {
    const router = TestBed.inject(Router);
    await router.navigateByUrl('/artesano');
    expect(router.url).toBe('/login');
  });

  it('un comprador tampoco puede entrar a /artesano', async () => {
    TestBed.inject(TiendaService).iniciarSesion('comprador@gmail.com', 'comprador');
    const router = TestBed.inject(Router);
    await router.navigateByUrl('/artesano');
    expect(router.url).toBe('/login');
  });

  it('un artesano con sesión sí entra', async () => {
    TestBed.inject(TiendaService).iniciarSesion('ana@gmail.com', 'artesano');
    const router = TestBed.inject(Router);
    await router.navigateByUrl('/artesano');
    expect(router.url).toBe('/artesano');
  });
});
