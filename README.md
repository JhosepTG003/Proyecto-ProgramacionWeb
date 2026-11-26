# Maki Core

Tienda web de artesanías textiles del Valle del Mantaro, hecha con Angular y Signals (signal, computed, effect y Signal Forms). Tiene un backend en FastAPI y una base de datos SQL Server opcional: sin base de datos el backend guarda todo en memoria.

## Cómo ejecutarlo

Se usan **dos terminales abiertas a la vez** (backend y frontend). Una tercera es opcional, para las pruebas.

### 0. Comprobar que todo está instalado (cualquier terminal)

```powershell
node -v      # debe mostrar v20 o superior
npm -v
git --version
uv --version
```

Si alguno da error de "no se reconoce el comando", instálalo y **abre una terminal nueva** antes de volver a comprobar:

```powershell
winget install OpenJS.NodeJS.LTS      # Node.js y npm
winget install Git.Git                # Git
winget install astral-sh.uv           # uv (gestor de Python del backend)
```

Para usar la base de datos (opcional) también necesitas SQL Server, SSMS y el driver ODBC:

```powershell
Get-OdbcDriver -Name "*SQL Server*"   # debe aparecer "ODBC Driver 18 for SQL Server"
```

Sin base de datos, salta el paso 2.

### 1. Terminal 1: instalar dependencias del frontend (una sola vez)

En la carpeta del frontend (la raíz del proyecto):

```powershell
npm install
```

### 2. Base de datos (opcional, solo la primera vez)

Si no quieres base de datos, sáltate este paso: el backend funcionará en memoria y todo se borrará al reiniciarlo.

1. En SSMS, conéctate a tu servidor, crea la base `maki` y ejecuta `database-MakiCore/database-MakiCore-sqlserver.sql`.
2. Comprueba que existan las tablas:
   ```sql
   USE maki;
   SELECT name FROM sys.tables;
   ```
3. Al arrancar el backend conectado, `seed.py` carga solo los datos de ejemplo (3 usuarios, 3 fibras y 2 prendas). Si necesitas empezar de cero, vacía las tablas antes:
   ```sql
   USE maki;
   DELETE FROM pedido_items; DELETE FROM pedidos; DELETE FROM sesiones;
   DELETE FROM prendas; DELETE FROM fibras;
   DELETE FROM usuarios; DELETE FROM artesanos;
   ```

### 3. Terminal 1: arrancar el backend

En `Backend-MakiCore\backend`. Cada línea va por separado:

```powershell
uv sync
```

Solo si usas base de datos, define la conexión en **esta misma terminal**:

```powershell
$env:DATABASE_URL = "DRIVER={ODBC Driver 18 for SQL Server};
SERVER=localhost\SQLEXPRESS;
DATABASE=maki;
Trusted_Connection=yes;
TrustServerCertificate=yes;"
```

Lo único que cambia entre computadoras es `SERVER`:

- `localhost\SQLEXPRESS` si tienes SQL Server Express.
- `.` si es la instancia por defecto (por ejemplo, en la PC del laboratorio).

Para saber cuál es el tuyo y qué otras partes pueden cambiar (driver, autenticación), mira `Backend-MakiCore/backend/README.md`, sección "Cadena de conexión".

Y arranca:

```powershell
uv run uvicorn backend.main:app --reload --port 8000
```

Déjala abierta. Verifica en el navegador:

- http://localhost:8000/salud debe responder `{"estado":"ok"}`
- http://localhost:8000/docs abre Swagger

### 4. Terminal 2 (nueva): arrancar el frontend

Abre otra terminal, ve a la carpeta del frontend y ejecuta:

```powershell
npm start        # ng serve -> http://localhost:4200
```

Entra a **http://localhost:4200** (no uses 127.0.0.1).

### 5. Usuarios de prueba

| Rol | Correo | Clave |
|---|---|---|
| Artesano | taller.godino@maki.pe | maki123 |
| Artesano | taller.palacios@maki.pe | maki123 |
| Comprador | comprador@maki.pe | maki123 |

### 6. Pruebas y compilación (terminal 3, opcional)

```powershell
npm test             # pruebas del frontend (Vitest), en la carpeta del frontend
npm run build        # compilación de producción, en la carpeta del frontend
uv run pytest        # pruebas del backend, en Backend-MakiCore\backend
```

Para detener cualquier servidor: `Ctrl+C` en su terminal.

## Pantallas (rutas)

| Ruta | Qué muestra | Acceso |
|---|---|---|
| `/catalogo` | Catálogo con filtros por fibra (página inicial) | Público |
| `/carrito` | Carrito, zona de envío, total y división 20/80 | Público (pagar: comprador) |
| `/login` | Inicio y cierre de sesión | Público |
| `/artesano` | Registro de prendas (con foto y stock) y nuevas fibras | Solo artesano (`artesanoGuard`) |

Las rutas cargan de forma diferida y cualquier ruta desconocida lleva al catálogo.

## Estructura

```
Backend-MakiCore/backend/   API FastAPI (repositorios, esquemas, seguridad, seed.py)
database-MakiCore/          Script SQL de la base de datos
src/app/
├── tienda.service.ts   Estado de la tienda: sesión, catálogo, carrito, moneda, envío y pedido
├── configuracion.ts    Valores de negocio: tasa EUR, tarifas de envío, 20/80, límites
├── dinero.ts           Funciones de dinero en centavos (conversión y división 20/80)
├── artesano.guard.ts   Protege /artesano
├── app.routes.ts       Rutas
└── catalogo/ carrito/ login/ artesano/   Un componente por pantalla
```

## Decisiones importantes

- **Dinero en centavos enteros.** Los precios y totales se guardan como enteros (15000 = $150.00) para evitar errores de decimales. La división 20/80 siempre suma exactamente el subtotal.
- **Tipado estricto.** `strict` y `strictTemplates` activados; `Rol`, `Moneda`, `Zona` y `EstadoPedido` son uniones de texto, así que un error de escritura no compila.
- **El correo del artesano nunca se muestra.** El catálogo usa el nombre público del taller (por ejemplo, "Taller Godiño Yanqui").
- **Stock por prenda.** El artesano indica las unidades al registrar la prenda. El catálogo muestra "Stock", "¡Últimas n!" (3 o menos) o "Agotado" y desactiva "Añadir" cuando no se puede. El carrito nunca pasa del stock (ni de 10 por prenda), y al pagar se revisa el stock y se descuenta. Con el pedido ya pagado el carrito no se edita hasta pulsar "Hacer un nuevo pedido".
- **Un solo rol por sesión.** Para cambiar de rol hay que cerrar sesión (botón en el menú).

## Limitaciones

- **El rol lo asigna el backend.** El inicio de sesión valida correo y clave contra el backend, que devuelve un token; el guard del frontend solo mejora la experiencia.
- **Sin `DATABASE_URL` nada persiste.** El backend guarda todo en memoria y al reiniciarlo se pierden usuarios nuevos, prendas y pedidos. Con la base conectada los datos se conservan.
- Las fotos aceptan JPG, PNG o WebP de hasta 2 MB.
- Bootstrap, los iconos y las fuentes se cargan desde CDN (`src/index.html`).