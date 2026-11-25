from backend.schemas.enums import Moneda, Zona
from backend.services.dinero import convertir, costo_envio, dividir_venta


def test_convertir_usd_no_cambia():
    assert convertir(15000, Moneda.USD) == 15000


def test_convertir_a_euros():
    assert convertir(15000, Moneda.EUR) == 13800
    assert convertir(4500, Moneda.EUR) == 4140
    assert convertir(2500, Moneda.EUR) == 2300


def test_division_20_80_exacta():
    assert dividir_venta(15000) == (3000, 12000)
    assert dividir_venta(0) == (0, 0)


def test_division_siempre_suma_el_monto():
    for monto in (1, 7, 99, 12345, 999_999):
        plataforma, cooperativa = dividir_venta(monto)
        assert plataforma + cooperativa == monto


def test_redondeo_mitad_hacia_arriba_como_javascript():
    # 2.5 -> 3 (round() de Python daría 2)
    assert dividir_venta(5, 50) == (3, 2)


def test_envio_por_zona_y_carrito_vacio():
    assert costo_envio(10000, Zona.AMERICA, Moneda.USD) == 2500
    assert costo_envio(10000, Zona.EUROPA, Moneda.USD) == 3000
    assert costo_envio(10000, Zona.OTROS, Moneda.EUR) == 3680
    assert costo_envio(0, Zona.OTROS, Moneda.USD) == 0
