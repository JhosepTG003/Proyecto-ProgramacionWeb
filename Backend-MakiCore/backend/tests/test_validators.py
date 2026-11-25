import base64

import pytest

from backend.validators import clave_fibra, normalizar_fibra, validar_correo, validar_foto

PNG_MINIMO = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 20).decode()


@pytest.mark.parametrize("correo", ["ana@gmail.com", "a.b+c@mi-taller.com.pe"])
def test_correos_validos(correo):
    assert validar_correo(correo) == ""


@pytest.mark.parametrize(
    "correo, fragmento",
    [
        ("", "Escribe tu correo"),
        ("anagmail.com", "Falta el símbolo @"),
        ("a@b@c.com", "solo puede tener un @"),
        ("@gmail.com", "usuario antes del @"),
        ("ana@", "dominio después del @"),
        ("ana..x@gmail.com", "caracteres no válidos"),
        ("ana@gmial.com", "@gmail.com"),
        ("ana@dominio", "no es válido"),
    ],
)
def test_correos_invalidos(correo, fragmento):
    assert fragmento in validar_correo(correo)


def test_normalizar_fibra():
    assert normalizar_fibra("  VICUÑA ") == "Vicuña"
    assert normalizar_fibra("lana   de  oveja") == "Lana de oveja"


@pytest.mark.parametrize("texto", ["ab", "x" * 31, "Alpaca2", "Lla$ma"])
def test_fibra_invalida(texto):
    with pytest.raises(ValueError):
        normalizar_fibra(texto)


def test_clave_fibra_ignora_tildes_y_mayusculas():
    assert clave_fibra("Vicuña") == clave_fibra("VICUNA") == "vicuna"


def test_foto_valida():
    url = f"data:image/png;base64,{PNG_MINIMO}"
    assert validar_foto(url) == url


@pytest.mark.parametrize(
    "valor",
    [
        "http://sitio.com/foto.png",
        "data:image/gif;base64,AAAA",
        f"data:image/jpeg;base64,{PNG_MINIMO}",  # declara JPG pero el contenido es PNG
        "data:image/png;base64,@@@@",
    ],
)
def test_foto_invalida(valor):
    with pytest.raises(ValueError):
        validar_foto(valor)


def test_foto_demasiado_grande():
    grande = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * (2 * 1024 * 1024)).decode()
    with pytest.raises(ValueError, match="pesa más"):
        validar_foto(f"data:image/png;base64,{grande}")
