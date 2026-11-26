# Maki Core · Backend

API REST (FastAPI + Uvicorn) de la tienda de artesanías textiles **Maki Core**.
Sigue la estructura del backend de ejemplo: `apis → services → repositories`, con `schemas`
(Pydantic) en los bordes. Guarda en **SQL Server** si existe `DATABASE_URL`; si no, usa
**memoria** (se pierde al reiniciar).

## Base de datos (SQL Server)

El esquema está en `../../database-MakiCore/database-MakiCore.sql` (crea la base `maki`).

1. En SSMS, conéctate a tu servidor, crea la base `maki` y ejecuta ese script.
2. El nombre del servidor **cambia de una computadora a otra** (`.`, `.\SQLEXPRESS`, etc.). Para saber cuál es el tuyo, mira el README de la raíz, sección "Averiguar el nombre de tu servidor SQL".
3. Comprueba que existan las tablas:

   ```sql
   USE maki;
   SELECT name FROM sys.tables;
   ```

4. Define la conexión en la **misma terminal** donde arrancas el backend (cada línea por separado):

   ```powershell
   $env:DATABASE_URL = "DRIVER={ODBC Driver 18 for SQL Server};
   SERVER=localhost\SQLEXPRESS;
   DATABASE=maki;
   Trusted_Connection=yes;
   TrustServerCertificate=yes;"
   ```

   ```powershell
   uv run uvicorn backend.main:app --reload --port 8000
   ```

### Cadena de conexión: qué cambiar en otra máquina

| Parte | Valor | ¿Cambiar? |
|---|---|---|
| `DRIVER` | `{ODBC Driver 18 for SQL Server}` | Solo si tienes otra versión instalada |
| `SERVER` | `localhost\SQLEXPRESS` | **Sí.** Es el nombre de tu servidor SQL (ver abajo) |
| `DATABASE` | `maki` | No |
| `Trusted_Connection` | `yes` | Usa tu usuario de Windows, sin clave. Si tu servidor usa usuario y clave de SQL, cámbialo por `UID=usuario;PWD=clave;` |
| `TrustServerCertificate` | `yes` | No |

**Saber qué poner en `SERVER`:** es el mismo nombre que usas para conectarte en SSMS. Si no lo sabes:

```powershell
Get-Service | Where-Object { $_.Name -like "*SQL*" }
```

| Servicio en `Running` | Valor de `SERVER` |
|---|---|
| `MSSQLSERVER` | `localhost` |
| `MSSQL$SQLEXPRESS` | `localhost\SQLEXPRESS` |
| `MSSQL$OTRONOMBRE` | `localhost\OTRONOMBRE` |

**Saber qué driver tienes instalado:**

```powershell
Get-OdbcDriver -Name "*SQL Server*"
```

Si no aparece `ODBC Driver 18 for SQL Server`, instálalo o cambia el nombre en `DRIVER` por el que aparezca (por ejemplo `ODBC Driver 17 for SQL Server`).

Los datos de ejemplo se cargan solo si la base no tiene usuarios. Si necesitas empezar de cero, vacía las tablas antes de arrancar:

```sql
USE maki;
DELETE FROM pedido_items; DELETE FROM pedidos; DELETE FROM sesiones;
DELETE FROM prendas; DELETE FROM fibras;
DELETE FROM usuarios; DELETE FROM artesanos;
```

Las pruebas (`uv run pytest`) corren en memoria; no necesitan base de datos. Los repositorios de SQL Server están en `repositories/` junto a los de memoria y tienen los mismos métodos.

## Cómo ejecutarlo

Con **uv** (recomendado):

```powershell
uv sync
uv run uvicorn backend.main:app --reload --port 8000
# o, equivalente:  uv run backend
```

Sin uv:

```powershell
python -m venv .venv
.venv\Scripts\activate
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
├── repositories/      Almacenes en memoria y en SQL Server: usuarios, sesiones, prendas, fibras, pedidos
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

## Conexión con el frontend

El frontend (`src/app/api.service.ts`) llama a esta API con `HttpClient`, y un interceptor
(`auth.interceptor.ts`) agrega `Authorization: Bearer <token>`. El rol se fija al registrarse y
`/auth/login` lo devuelve. El carrito sigue en el navegador; al pagar se envía
`{ items: [{prenda_id, cantidad}], moneda, zona }`. Los montos llegan en centavos.

## Limitaciones

- **Sin `DATABASE_URL` todo es en memoria:** al reiniciar se pierden usuarios, sesiones, prendas y
  pedidos (los de ejemplo se vuelven a cargar).
- Funciona con **un solo proceso** (no uses varios `--workers`): el candado de stock y de códigos
  (`threading.Lock`) vive dentro del proceso. Pagar descuenta cada prenda y guarda el pedido en
  transacciones separadas: si el servidor se cae justo en medio, el stock podría quedar descontado
  sin pedido.
- **El pago es simulado** (siempre se aprueba), como en el prototipo.
- La tasa EUR es fija en `config.py`.