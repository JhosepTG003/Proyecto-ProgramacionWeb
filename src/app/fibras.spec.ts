import { TestBed } from '@angular/core/testing';
import { TiendaService } from './tienda.service';

describe('Nuevas fibras', () => {
  it('agrega una fibra nueva con formato uniforme', () => {
    const t = TestBed.inject(TiendaService);
    const r = t.agregarFibra('  VICUÑA ');
    expect(r.ok).toBe(true);
    expect(r.fibra).toBe('Vicuña');
    expect(t.fibras()).toContain('Vicuña');
  });

  it('no permite duplicados (ignora mayúsculas y tildes)', () => {
    const t = TestBed.inject(TiendaService);
    expect(t.agregarFibra('alpaca').ok).toBe(false);
    t.agregarFibra('Vicuña');
    expect(t.agregarFibra('vicuna').ok).toBe(false);
    expect(t.fibras().filter((f) => f.startsWith('Vicu')).length).toBe(1);
  });

  it('rechaza textos vacíos, cortos o con números', () => {
    const t = TestBed.inject(TiendaService);
    expect(t.agregarFibra('').ok).toBe(false);
    expect(t.agregarFibra('ab').ok).toBe(false);
    expect(t.agregarFibra('Fibra123').ok).toBe(false);
  });
});
