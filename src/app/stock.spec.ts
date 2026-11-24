import { TestBed } from '@angular/core/testing';
import { ArtesanoComponent } from './artesano/artesano.component';
import { CatalogoComponent } from './catalogo/catalogo.component';
import { TiendaService } from './tienda.service';

function prendaConStock(t: TiendaService, stock: number) {
  return t.registrarPrenda({
    nombre: 'Manta',
    artesano: 'Artesano ART-0009',
    artesanoId: 'ART-0009',
    fibra: 'Alpaca',
    tinte: 'Molle',
    precioCentavosUSD: 1000,
    stock,
  });
}

describe('Stock en el carrito', () => {
  it('no deja añadir más unidades que el stock y explica por qué', () => {
    const t = TestBed.inject(TiendaService);
    const p = prendaConStock(t, 2);
    expect(t.agregar(p.id, false)).toBe(true);
    expect(t.agregar(p.id, false)).toBe(true);
    expect(t.agregar(p.id, false)).toBe(false);
    expect(t.enCarrito(p.id)).toBe(2);
    expect(t.aviso()).toContain('stock disponible');
    expect(t.puedeAgregar(p.id)).toBe(false);
  });

  it('una prenda agotada no se puede añadir', () => {
    const t = TestBed.inject(TiendaService);
    const p = prendaConStock(t, 0);
    expect(t.agregar(p.id)).toBe(false);
    expect(t.totalPrendas()).toBe(0);
    expect(t.motivoNoAgregar(p.id)).toContain('agotada');
  });

  it('el límite es el menor entre el stock y el máximo por prenda', () => {
    const t = TestBed.inject(TiendaService);
    const p = prendaConStock(t, 50);
    for (let i = 0; i < t.maxPorPrenda; i++) t.agregar(p.id, false);
    expect(t.enCarrito(p.id)).toBe(t.maxPorPrenda);
    expect(t.motivoNoAgregar(p.id)).toContain('Máximo');
  });
});

describe('Stock al pagar', () => {
  function comprador() {
    const t = TestBed.inject(TiendaService);
    t.iniciarSesion('ana@gmail.com', 'comprador');
    return t;
  }

  it('pagar descuenta del stock lo que se compró', () => {
    const t = comprador();
    const p = prendaConStock(t, 5);
    t.agregar(p.id, false);
    t.agregar(p.id, false);
    t.pagar();
    expect(t.estadoPedido()).toBe('Aprobado');
    expect(t.prendas().find((x) => x.id === p.id)!.stock).toBe(3);
  });

  it('pagar dos veces el mismo pedido no descuenta dos veces', () => {
    const t = comprador();
    const p = prendaConStock(t, 5);
    t.agregar(p.id, false);
    t.pagar();
    t.pagar();
    expect(t.prendas().find((x) => x.id === p.id)!.stock).toBe(4);
  });

  it('con el pedido pagado no se puede editar el carrito hasta empezar otro', () => {
    const t = comprador();
    const p = prendaConStock(t, 5);
    t.agregar(p.id, false);
    t.pagar();
    expect(t.agregar(p.id, false)).toBe(false);
    t.quitar(p.id);
    expect(t.enCarrito(p.id)).toBe(1);

    t.nuevoPedido();
    expect(t.agregar(p.id, false)).toBe(true);
  });

  it('si el stock bajó antes de pagar, no cobra y no descuenta', () => {
    const t = comprador();
    const p = prendaConStock(t, 3);
    t.agregar(p.id, false);
    t.agregar(p.id, false);
    t.agregar(p.id, false);
    t.prendas.update((l) => l.map((x) => (x.id === p.id ? { ...x, stock: 1 } : x)));
    t.pagar();
    expect(t.estadoPedido()).toBe('Sin pedido');
    expect(t.mensajePedido()).toContain('No hay stock suficiente');
    expect(t.prendas().find((x) => x.id === p.id)!.stock).toBe(1);
  });

  it('agotar una prenda con la compra la deja sin poder añadirse', () => {
    const t = comprador();
    const p = prendaConStock(t, 1);
    t.agregar(p.id, false);
    t.pagar();
    t.nuevoPedido();
    expect(t.motivoNoAgregar(p.id)).toContain('agotada');
  });
});

describe('Stock en el catálogo', () => {
  it('muestra Agotado con el botón desactivado, y avisa cuando quedan pocas', async () => {
    const t = TestBed.inject(TiendaService);
    const agotada = prendaConStock(t, 0);
    const pocas = prendaConStock(t, 2);
    const fixture = TestBed.createComponent(CatalogoComponent);
    await fixture.whenStable();
    const tarjetas = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('.card'));
    const de = (id: string) =>
      tarjetas[t.prendas().findIndex((x) => x.id === id)] as HTMLElement;

    expect(de(agotada.id).textContent).toContain('Agotado');
    expect((de(agotada.id).querySelector('button') as HTMLButtonElement).disabled).toBe(true);
    expect(de(pocas.id).textContent).toContain('Últimas 2');
    expect((de(pocas.id).querySelector('button') as HTMLButtonElement).disabled).toBe(false);
  });

  it('el stock del catálogo baja después de una compra', async () => {
    const t = TestBed.inject(TiendaService);
    t.iniciarSesion('ana@gmail.com', 'comprador');
    t.agregar('poncho-andino', false);
    t.pagar();
    const fixture = TestBed.createComponent(CatalogoComponent);
    await fixture.whenStable();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Stock: 11'); // 12 - 1
  });
});

describe('Stock al registrar una prenda', () => {
  function montar() {
    const tienda = TestBed.inject(TiendaService);
    tienda.iniciarSesion('ana@gmail.com', 'artesano');
    const comp = TestBed.createComponent(ArtesanoComponent).componentInstance;
    return { tienda, comp };
  }
  const base = { nombre: 'Manta', fibra: 'Alpaca', tinte: 'Molle', precio: 10 };

  it('guarda el stock indicado', () => {
    const { tienda, comp } = montar();
    comp.modelo.set({ ...base, stock: 7 });
    comp.registrar();
    expect(tienda.prendas().at(-1)!.stock).toBe(7);
  });

  it('rechaza stock 0, negativo, con decimales o demasiado grande', () => {
    for (const stock of [0, -3, 1.5, 10000]) {
      const { tienda, comp } = montar();
      const antes = tienda.prendas().length;
      comp.modelo.set({ ...base, stock });
      comp.registrar();
      expect(tienda.prendas().length, 'stock ' + stock).toBe(antes);
      TestBed.resetTestingModule();
    }
  });
});
