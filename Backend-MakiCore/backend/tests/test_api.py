import base64

API = ""
PNG = "data:image/png;base64," + base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 20).decode()


def test_catalogo_publico_y_filtro(client):
    r = client.get(f"{API}/prendas")
    assert r.status_code == 200
    ids = {p["id"] for p in r.json()}
    assert {"poncho-andino", "chalina-hualhuas"} <= ids
    assert "correo" not in r.text  # el correo del artesano nunca se expone

    solo_alpaca = client.get(f"{API}/prendas", params={"fibra": "alpaca"}).json()
    assert [p["id"] for p in solo_alpaca] == ["poncho-andino"]
    assert len(client.get(f"{API}/prendas", params={"fibra": "Todas"}).json()) >= 2


def test_login_incorrecto_y_sin_token(client):
    r = client.post(f"{API}/auth/login", json={"correo": "comprador@maki.pe", "clave": "mala-clave"})
    assert r.status_code == 401
    assert client.get(f"{API}/auth/me").status_code == 401


def test_registro_valida_correo_y_duplicados(client):
    malo = client.post(f"{API}/auth/registro", json={"correo": "ana@gmial.com", "clave": "123456", "rol": "comprador"})
    assert malo.status_code == 422
    ok = client.post(f"{API}/auth/registro", json={"correo": "Nuevo@Gmail.com ", "clave": "123456", "rol": "artesano"})
    assert ok.status_code == 201
    assert ok.json()["usuario"]["artesano_id"] == "ART-0003"
    assert ok.json()["usuario"]["nombre_publico"] == "Artesano ART-0003"
    repetido = client.post(f"{API}/auth/registro", json={"correo": "nuevo@gmail.com", "clave": "123456", "rol": "comprador"})
    assert repetido.status_code == 409


def test_roles_se_respetan(client, comprador, artesano):
    cuerpo = {"nombre": "Manta", "fibra": "Alpaca", "tinte": "Natural", "precio_centavos_usd": 5000, "stock": 3}
    assert client.post(f"{API}/prendas", json=cuerpo).status_code == 401
    assert client.post(f"{API}/prendas", json=cuerpo, headers=comprador).status_code == 403
    assert client.get(f"{API}/pedidos/ventas", headers=comprador).status_code == 403
    assert client.post(f"{API}/pedidos", json={"items": [{"prenda_id": "poncho-andino", "cantidad": 1}]}, headers=artesano).status_code == 403


def test_artesano_registra_prenda_y_fibra_nueva(client, artesano):
    nueva = client.post(f"{API}/fibras", json={"nombre": "vicuña"}, headers=artesano)
    assert nueva.status_code == 201 and nueva.json()["nombre"] == "Vicuña"
    repetida = client.post(f"{API}/fibras", json={"nombre": "VICUNA"}, headers=artesano)
    assert repetida.status_code == 409

    r = client.post(
        f"{API}/prendas",
        json={"nombre": " Chullo ", "fibra": "Vicuña", "tinte": "Índigo", "precio_centavos_usd": 3500, "stock": 5, "foto": PNG},
        headers=artesano,
    )
    assert r.status_code == 201, r.text
    prenda = r.json()
    assert prenda["id"].startswith("MAKI-")
    assert prenda["artesano_id"] == "ART-0001" and prenda["artesano"] == "Taller Godiño Yanqui"
    assert prenda["nombre"] == "Chullo"
    assert client.get(f"{API}/prendas/{prenda['id']}").status_code == 200
    assert prenda["id"] in [p["id"] for p in client.get(f"{API}/prendas/mias", headers=artesano).json()]


def test_prenda_invalida(client, artesano):
    base = {"nombre": "X", "fibra": "Alpaca", "tinte": "Y", "precio_centavos_usd": 100, "stock": 1}
    for cambio in ({"precio_centavos_usd": 0}, {"stock": 0}, {"foto": "http://x.com/a.png"}, {"fibra": "Alpaca1"}):
        assert client.post(f"{API}/prendas", json={**base, **cambio}, headers=artesano).status_code == 422


def test_cotizar_en_euros_con_envio_a_europa(client):
    r = client.post(
        f"{API}/pedidos/cotizar",
        json={"items": [{"prenda_id": "poncho-andino", "cantidad": 2}], "moneda": "EUR", "zona": "Europa"},
    )
    assert r.status_code == 200, r.text
    c = r.json()
    assert c["subtotal"] == 2 * 13800
    assert c["envio"] == 2760  # 3000 centavos USD * 0.92
    assert c["total"] == c["subtotal"] + c["envio"]
    assert c["plataforma"] + c["cooperativa"] == c["subtotal"]
    assert c["plataforma"] == 5520


def test_pago_descuenta_stock_y_notifica_al_artesano(client, comprador, artesano):
    antes = client.get(f"{API}/prendas/chalina-hualhuas").json()["stock"]
    r = client.post(
        f"{API}/pedidos",
        json={"items": [{"prenda_id": "chalina-hualhuas", "cantidad": 3}], "zona": "America"},
        headers=comprador,
    )
    assert r.status_code == 201, r.text
    pedido = r.json()
    assert pedido["estado"] == "Aprobado" and pedido["subtotal"] == 3 * 4500
    assert pedido["total"] == 3 * 4500 + 2500
    assert "Pago aprobado" in pedido["mensaje"]

    assert client.get(f"{API}/prendas/chalina-hualhuas").json()["stock"] == antes - 3
    assert pedido["id"] in [p["id"] for p in client.get(f"{API}/pedidos/mis-pedidos", headers=comprador).json()]
    assert client.get(f"{API}/pedidos/{pedido['id']}", headers=comprador).status_code == 200

    # La venta le aparece al artesano dueño (ART-0002), no a otro.
    otro = client.post(f"{API}/auth/login", json={"correo": "taller.palacios@maki.pe", "clave": "maki123"}).json()
    ventas = client.get(f"{API}/pedidos/ventas", headers={"Authorization": f"Bearer {otro['access_token']}"}).json()
    assert any(v["pedido_id"] == pedido["id"] and v["cantidad"] == 3 for v in ventas)
    assert not any(v["pedido_id"] == pedido["id"] for v in client.get(f"{API}/pedidos/ventas", headers=artesano).json())


def test_no_se_vende_mas_del_stock_ni_mas_de_10(client, comprador):
    pedido = {"items": [{"prenda_id": "poncho-andino", "cantidad": 10}]}
    client.post(f"{API}/pedidos", json=pedido, headers=comprador)  # deja 2 de 12
    r = client.post(f"{API}/pedidos", json=pedido, headers=comprador)
    assert r.status_code == 422 and "stock suficiente" in r.json()["detail"]

    assert client.post(f"{API}/pedidos", json={"items": [{"prenda_id": "poncho-andino", "cantidad": 11}]}, headers=comprador).status_code == 422
    assert client.post(f"{API}/pedidos", json={"items": [{"prenda_id": "no-existe", "cantidad": 1}]}, headers=comprador).status_code == 404


def test_configuracion(client):
    c = client.get(f"{API}/configuracion").json()
    assert c["porcentaje_plataforma"] == 20 and c["tasa_eur"] == 0.92
    assert c["tarifas_envio_centavos_usd"]["Europa"] == 3000


def test_logout_invalida_la_sesion(client):
    r = client.post(f"{API}/auth/login", json={"correo": "comprador@maki.pe", "clave": "maki123"})
    cab = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert client.get(f"{API}/auth/me", headers=cab).json()["rol"] == "comprador"
    assert "clave" not in client.get(f"{API}/auth/me", headers=cab).text
    assert client.post(f"{API}/auth/logout", headers=cab).status_code == 204
    assert client.get(f"{API}/auth/me", headers=cab).status_code == 401
