import { TestBed } from '@angular/core/testing';
import { ArtesanoComponent } from './artesano/artesano.component';
import { MAX_FOTO_BYTES } from './configuracion';
import { TiendaService } from './tienda.service';

// PNG de 1x1 píxel
const PNG_1X1 = Uint8Array.from(atob('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='), (c) => c.charCodeAt(0));

function evento(archivo?: File) {
  const campo = document.createElement('input');
  campo.type = 'file';
  Object.defineProperty(campo, 'files', { value: archivo ? [archivo] : [] });
  return { target: campo } as unknown as Event;
}

describe('Fotografía de la prenda', () => {
  function montar() {
    const tienda = TestBed.inject(TiendaService);
    tienda.iniciarSesion('ana@gmail.com', 'artesano');
    const fixture = TestBed.createComponent(ArtesanoComponent);
    return { tienda, comp: fixture.componentInstance, fixture, el: fixture.nativeElement as HTMLElement };
  }

  it('acepta una imagen válida y la guarda como data URL', async () => {
    const { comp } = montar();
    comp.elegirFoto(evento(new File([PNG_1X1], 'a.png', { type: 'image/png' })));
    await vi.waitFor(() => expect(comp.foto()).toMatch(/^data:image\/png;base64,/));
    expect(comp.errorFoto()).toBe('');
  });

  it('rechaza archivos que no son JPG, PNG o WebP (incluye SVG)', () => {
    const { comp } = montar();
    comp.elegirFoto(evento(new File(['<svg/>'], 'a.svg', { type: 'image/svg+xml' })));
    expect(comp.foto()).toBe('');
    expect(comp.errorFoto()).toContain('JPG, PNG o WebP');
  });

  it('rechaza imágenes de más de 2 MB', () => {
    const { comp } = montar();
    const grande = new File([new Uint8Array(MAX_FOTO_BYTES + 1)], 'g.jpg', { type: 'image/jpeg' });
    comp.elegirFoto(evento(grande));
    expect(comp.foto()).toBe('');
    expect(comp.errorFoto()).toContain('2 MB');
  });

  it('la prenda se registra con foto, en centavos, y la foto se limpia después', async () => {
    const { tienda, comp } = montar();
    comp.elegirFoto(evento(new File([PNG_1X1], 'a.png', { type: 'image/png' })));
    await vi.waitFor(() => expect(comp.foto()).not.toBe(''));
    comp.modelo.set({ nombre: 'Manta', fibra: 'Alpaca', tinte: 'Molle', precio: 19.99 });
    comp.registrar();
    const nueva = tienda.prendas().at(-1)!;
    expect(nueva.precioCentavosUSD).toBe(1999);
    expect(nueva.foto).toMatch(/^data:image\/png/);
    expect(comp.foto()).toBe('');
  });

  it('sin foto, la prenda se registra igual', () => {
    const { tienda, comp } = montar();
    comp.modelo.set({ nombre: 'Manta', fibra: 'Alpaca', tinte: 'Molle', precio: 10 });
    comp.registrar();
    expect(tienda.prendas().at(-1)!.foto).toBeUndefined();
  });

  it('rechaza precios fuera de rango', () => {
    const { tienda, comp } = montar();
    comp.modelo.set({ nombre: 'Manta', fibra: 'Alpaca', tinte: 'Molle', precio: 1e9 });
    comp.registrar();
    expect(tienda.prendas().length).toBe(2);
    expect(comp.mensaje()).toBe('Completa todos los campos.');
  });
});
