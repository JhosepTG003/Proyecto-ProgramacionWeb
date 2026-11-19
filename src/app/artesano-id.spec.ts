import { TestBed } from '@angular/core/testing';
import { TiendaService } from './tienda.service';

describe('ID único de artesano', () => {
  it('asigna un ID nuevo a cada artesano', () => {
    const t = TestBed.inject(TiendaService);
    t.iniciarSesion('ana@gmail.com', 'artesano');
    const idAna = t.idArtesano();
    t.cerrarSesion();
    t.iniciarSesion('luis@gmail.com', 'artesano');
    expect(idAna).toBe('ART-0003');
    expect(t.idArtesano()).toBe('ART-0004');
  });

  it('el mismo correo siempre recibe el mismo ID', () => {
    const t = TestBed.inject(TiendaService);
    t.iniciarSesion('ana@gmail.com', 'artesano');
    const primero = t.idArtesano();
    t.cerrarSesion();
    t.iniciarSesion('ana@gmail.com', 'artesano');
    expect(t.idArtesano()).toBe(primero);
  });

  it('un comprador no recibe ID y la prenda guarda el ID del artesano', () => {
    const t = TestBed.inject(TiendaService);
    t.iniciarSesion('comprador@gmail.com', 'comprador');
    expect(t.idArtesano()).toBe('');
    t.cerrarSesion();
    t.iniciarSesion('ana@gmail.com', 'artesano');
    const p = t.registrarPrenda({ nombre: 'Manta', artesano: t.usuario(), artesanoId: t.idArtesano(), fibra: 'Alpaca', tinte: 'Molle', precioUSD: 50 });
    expect(p.artesanoId).toBe('ART-0003');
  });
});
