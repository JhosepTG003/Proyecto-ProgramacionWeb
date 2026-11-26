import { convertir, dividirVenta, usdACentavos } from './dinero';

describe('Dinero en centavos', () => {
  it('convierte USD con decimales a centavos enteros sin error de float', () => {
    expect(usdACentavos(19.99)).toBe(1999);
    expect(usdACentavos(0.1 + 0.2)).toBe(30); // en float: 0.30000000000000004
  });

  it('convierte a EUR redondeando al centavo', () => {
    expect(convertir(8000, 'EUR')).toBe(7360);
    expect(convertir(1999, 'EUR')).toBe(1839); // 1839.08 -> 1839
    expect(convertir(1999, 'USD')).toBe(1999);
  });

  it('la división 20/80 siempre suma exactamente el monto', () => {
    expect(dividirVenta(10000)).toEqual({ plataforma: 2000, cooperativa: 8000 });
    for (const monto of [0, 1, 7, 33, 999, 1999, 12345]) {
      const { plataforma, cooperativa } = dividirVenta(monto);
      expect(plataforma + cooperativa).toBe(monto);
      expect(Number.isInteger(plataforma)).toBe(true);
    }
  });
});
