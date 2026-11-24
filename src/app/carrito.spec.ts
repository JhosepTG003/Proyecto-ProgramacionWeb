import { TestBed } from '@angular/core/testing';
import { MAX_CANTIDAD_POR_PRENDA } from './configuracion';
import { TiendaService } from './tienda.service';

// Catálogo inicial: 'poncho-andino' = $150.00, 'chalina-hualhuas' = $45.00 (en centavos: 15000 y 4500).
describe('Carrito y totales', () => {
  const crear = () => TestBed.inject(TiendaService);

  it('con el carrito vacío todo vale 0, también el envío', () => {
    const t = crear();
    expect(t.totalPrendas()).toBe(0);
    expect(t.subtotal()).toBe(0);
    expect(t.envio()).toBe(0);
    expect(t.total()).toBe(0);
  });

  it('suma cantidades y subtotal', () => {
    const t = crear();
    t.agregar('poncho-andino');
    t.agregar('chalina-hualhuas');
    t.agregar('chalina-hualhuas');
    expect(t.totalPrendas()).toBe(3);
    expect(t.subtotal()).toBe(15000 + 2 * 4500);
  });

  it('quitar baja la cantidad y elimina la línea al llegar a 0', () => {
    const t = crear();
    t.agregar('poncho-andino');
    t.agregar('poncho-andino');
    t.quitar('poncho-andino');
    expect(t.enCarrito('poncho-andino')).toBe(1);
    t.quitar('poncho-andino');
    expect(t.lineas().length).toBe(0);
  });

  it('ignora prendas que no existen', () => {
    const t = crear();
    expect(t.agregar('no-existe')).toBe(false);
    expect(t.totalPrendas()).toBe(0);
  });

  it('no deja pasar del máximo por prenda y avisa', () => {
    const t = crear();
    for (let i = 0; i < MAX_CANTIDAD_POR_PRENDA; i++) expect(t.agregar('poncho-andino', false)).toBe(true);
    expect(t.agregar('poncho-andino', false)).toBe(false);
    expect(t.enCarrito('poncho-andino')).toBe(MAX_CANTIDAD_POR_PRENDA);
    expect(t.aviso()).toContain('Máximo');
  });

  it('el aviso "se añadió" solo sale cuando se pide', () => {
    const t = crear();
    t.agregar('poncho-andino', false);
    expect(t.aviso()).toBe('');
    t.agregar('poncho-andino');
    expect(t.aviso()).toContain('se añadió al carrito');
  });
});

describe('Envío por zona (RF010)', () => {
  it('cobra la tarifa fija de cada zona', () => {
    const t = TestBed.inject(TiendaService);
    t.agregar('chalina-hualhuas');

    t.modeloEnvio.set({ zona: 'America' });
    expect(t.envio()).toBe(2500);
    t.modeloEnvio.set({ zona: 'Europa' });
    expect(t.envio()).toBe(3000);
    t.modeloEnvio.set({ zona: 'Otros' });
    expect(t.envio()).toBe(4000);
    expect(t.total()).toBe(4500 + 4000);
  });

  it('el envío se convierte a EUR y el subtotal también', () => {
    const t = TestBed.inject(TiendaService);
    t.agregar('poncho-andino');
    t.modeloEnvio.set({ zona: 'Europa' });
    t.cambiarMoneda('EUR');
    expect(t.subtotal()).toBe(13800); // 150 x 0.92 = 138.00
    expect(t.envio()).toBe(2760); // 30 x 0.92 = 27.60
    expect(t.total()).toBe(16560);
    expect(t.mostrar(t.total())).toBe('€165.60');
  });
});

describe('División 20/80 (RF021)', () => {
  it('reparte el subtotal sin contar el envío', () => {
    const t = TestBed.inject(TiendaService);
    t.agregar('poncho-andino');
    expect(t.plataforma()).toBe(3000);
    expect(t.cooperativa()).toBe(12000);
    expect(t.plataforma() + t.cooperativa()).toBe(t.subtotal());
  });

  it('no pierde centavos con montos que no se dividen exacto', () => {
    const t = TestBed.inject(TiendaService);
    t.registrarPrenda({ nombre: 'Prueba', artesano: 'X', artesanoId: 'ART-0009', fibra: 'Alpaca', tinte: 'Molle', precioCentavosUSD: 7, stock: 5 });
    t.agregar('MAKI-0001');
    expect(t.subtotal()).toBe(7);
    expect(t.plataforma() + t.cooperativa()).toBe(7);
  });
});

describe('Pagar', () => {
  it('con carrito vacío no aprueba', () => {
    const t = TestBed.inject(TiendaService);
    t.iniciarSesion('ana@gmail.com', 'comprador');
    t.pagar();
    expect(t.estadoPedido()).toBe('Sin pedido');
    expect(t.mensajePedido()).toContain('vacío');
  });

  it('sin sesión no aprueba', () => {
    const t = TestBed.inject(TiendaService);
    t.agregar('poncho-andino');
    t.pagar();
    expect(t.estadoPedido()).toBe('Sin pedido');
    expect(t.mensajePedido()).toContain('comprador');
  });

  it('un artesano no puede pagar', () => {
    const t = TestBed.inject(TiendaService);
    t.iniciarSesion('luis@gmail.com', 'artesano');
    t.agregar('poncho-andino');
    t.pagar();
    expect(t.estadoPedido()).toBe('Sin pedido');
  });

  it('un comprador con carrito lleno aprueba, y "nuevo pedido" lo reinicia', () => {
    const t = TestBed.inject(TiendaService);
    t.iniciarSesion('ana@gmail.com', 'comprador');
    t.agregar('poncho-andino');
    t.pagar();
    expect(t.estadoPedido()).toBe('Aprobado');
    t.nuevoPedido();
    expect(t.estadoPedido()).toBe('Sin pedido');
    expect(t.totalPrendas()).toBe(0);
  });
});
