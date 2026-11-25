# Maki Core · Backend

API REST (FastAPI + Uvicorn) de la tienda de artesanías textiles **Maki Core**.
Sigue la estructura del backend de ejemplo: `apis → services → repositories`, con `schemas`
(Pydantic) en los bordes y **almacenamiento en memoria** (se pierde al reiniciar).

## Cómo ejecutarlo

Con **uv** (recomendado):

```bash
uv sync
uv run uvicorn backend.main:app --reload --port 8000
# o, equivalente:  uv run backend
```

Sin uv:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .
uvicorn backend.main:app --reload --port 8000
```

- Swagger: http://localhost:8000/docs
- Estado: http://localhost:8000/salud
- Pruebas: `uv run pytest`

Como la memoria empieza vacía, al arrancar se cargan datos de ejemplo
(`SEED_DEMO_DATA=false` lo desactiva). Todos usan la clave `maki123`:

| Correo                    | Rol       | Notas                              |
| ------------------------- | --------- | ---------------------------------- |
| `taller.godino@maki.pe`   | artesano  | ART-0001 · Taller Godiño Yanqui    |
| `taller.palacios@maki.pe` | artesano  | ART-0002 · Taller Palacios Yalico  |
| `comprador@maki.pe`       | comprador |                                    |

## Estructura

```
src/backend/
├── main.py            App, CORS, routers, manejadores de excepciones, arranque
├── config.py          Reglas de negocio (tasa EUR, envío, 20/80, límites) y variables de entorno
├── seed.py            Datos de ejemplo
├── security.py        Hash de contraseñas (PBKDF2) y tokens de sesión
├── validators.py      Correo, fibra y foto
├── apis/              Routers: auth, prendas, fibras, pedidos, configuracion (+ dependencies)
├── services/          Reglas de negocio: auth, prendas, fibras, pedidos, dinero, exceptions
├── repositories/      Almacenes en memoria: usuarios, sesiones, prendas, fibras, pedidos
└── schemas/           Entradas/salidas: enums, usuarios, auth, prendas, fibras, pedidos, configuracion
```

## Endpoints

| Método y ruta               | Acceso    | Qué hace |
| --------------------------- | --------- | -------- |
| `POST /auth/registro`       | Público   | Crea cuenta con rol y devuelve token |
| `POST /auth/login`          | Público   | Devuelve token (el rol lo asigna el servidor) |
| `POST /auth/logout`         | Sesión    | Cierra la sesión |
| `GET  /auth/me`             | Sesión    | Usuario actual |
| `GET  /prendas?fibra=`      | Público   | Catálogo; `Todas` = sin filtro |
| `GET  /prendas/{id}`        | Público   | Una prenda |
| `GET  /prendas/mias`        | Artesano  | Prendas del artesano con sesión |
| `POST /prendas`             | Artesano  | Registra prenda (el `id` es el código QR `MAKI-0001`) |
| `GET  /fibras`              | Público   | Lista de fibras |
| `POST /fibras`              | Artesano  | Agrega fibra (normaliza, sin duplicados) |
| `POST /pedidos/cotizar`     | Público   | Subtotal, envío, total y división 20/80, sin cobrar |
| `POST /pedidos`             | Comprador | Paga: valida y descuenta stock, guarda el pedido |
| `GET  /pedidos/mis-pedidos` | Comprador | Historial |
| `GET  /pedidos/{id}`        | Comprador | Un pedido propio |
| `GET  /pedidos/ventas`      | Artesano  | Ventas de sus prendas |
| `GET  /configuracion`       | Público   | Tasa, tarifas y límites |

Las rutas protegidas usan `Authorization: Bearer <token>`.

## Reglas que antes vivían en el frontend

- Dinero en **centavos enteros**; USD→EUR (0.92) con el mismo redondeo que JavaScript.
- **División 20/80** sobre el subtotal (el envío no entra); siempre suma exacto.
- **Envío fijo por zona** (América 25, Europa 30, Otros 40 USD).
- **Stock:** máximo 10 por prenda y nunca más que el stock. Validar y descontar ocurre dentro
  de un candado (`threading.Lock`), así dos pagos simultáneos no se llevan el mismo stock.
- El correo del artesano **nunca** sale en el catálogo; solo su nombre público e ID.
- ID de artesano `ART-000N` y código de prenda `MAKI-000N` correlativos.
- Fibras sin duplicados por mayúsculas/tildes; foto JPG/PNG/WebP ≤ 2 MB comprobando su contenido.
- Correo con las mismas sugerencias de dominio (`gmial.com` → `gmail.com`).

## Cambios necesarios en el frontend

1. Reemplazar el estado local de `TiendaService` por `HttpClient` hacia `http://localhost:8000`
   y un interceptor que agregue `Authorization: Bearer <token>`.
2. **Login:** el rol se fija al registrarse y `/auth/login` lo devuelve; ya no se elige con el botón.
3. El carrito sigue en el frontend; al pagar se envía `{ items: [{prenda_id, cantidad}], moneda, zona }`.
4. Los montos llegan en centavos; el frontend solo les da formato.

## Limitaciones

- **Todo es en memoria:** al reiniciar se pierden usuarios, sesiones, prendas y pedidos
  (los de ejemplo se vuelven a cargar). Para persistir, solo hay que reemplazar las clases de
  `repositories/` por unas con base de datos: los services y las apis no cambian.
- Funciona con **un solo proceso** (no uses varios `--workers`: cada uno tendría su propia memoria).
- **El pago es simulado** (siempre se aprueba), como en el prototipo.
- La tasa EUR es fija en `config.py`.
