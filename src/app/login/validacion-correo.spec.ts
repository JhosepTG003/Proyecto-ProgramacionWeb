import { validarCorreo } from './login.component';

describe('validarCorreo', () => {
  it('acepta correos válidos (gmail y otros dominios)', () => {
    expect(validarCorreo('maki@gmail.com')).toBe('');
    expect(validarCorreo('ana.perez+tienda@outlook.com')).toBe('');
    expect(validarCorreo('contacto@cooperativa.com.pe')).toBe('');
    expect(validarCorreo('info@uni.edu.pe')).toBe('');
  });

  it('rechaza correos sin @ o con dominio incompleto', () => {
    expect(validarCorreo('makigmail.com')).toContain('@');
    expect(validarCorreo('maki@')).toContain('dominio');
    expect(validarCorreo('@gmail.com')).toContain('usuario');
    expect(validarCorreo('maki@gmail')).toContain('dominio');
    expect(validarCorreo('maki@gmail.')).toContain('dominio');
    expect(validarCorreo('maki@@gmail.com')).toContain('un @');
    expect(validarCorreo('ma ki@gmail.com')).toContain('caracteres');
  });

  it('sugiere el dominio correcto ante errores de tipeo', () => {
    expect(validarCorreo('maki@gmial.com')).toContain('gmail.com');
    expect(validarCorreo('maki@gmail.con')).toContain('gmail.com');
  });
});
