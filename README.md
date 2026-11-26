# Maki Core

Tienda web de artesanías textiles del Valle del Mantaro, hecha con Angular y Signals (`signal`, `computed`, `effect` y Signal Forms). Tiene un backend en FastAPI y utiliza SQL Server para almacenar los datos. La base de datos y sus tablas se crean automáticamente al iniciar el backend con una conexión válida.

## Cómo ejecutarlo

Se utilizan **dos terminales abiertas a la vez** (backend y frontend). Una tercera es opcional, para las pruebas.

### 0. Comprobar que todo está instalado

En cualquier terminal:

```powershell
node -v
npm -v
git --version
uv --version
```

Node.js debe ser versión 20 o superior.

Si alguno da error de "no se reconoce el comando", instálalo:

```powershell
winget install OpenJS.NodeJS.LTS
winget install Git.Git
winget install astral-sh.uv
```

Después, abre una terminal nueva y vuelve a comprobar.

Para utilizar SQL Server también necesitas SQL Server, el driver ODBC 18 y, opcionalmente, SSMS para administrar la base de datos.

Comprueba el driver con:

```powershell
Get-OdbcDriver -Name "*SQL Server*"
```

### 1. Instalar dependencias del frontend

En la carpeta raíz del proyecto:

```powershell
npm install
```

Este paso se realiza una sola vez, salvo que cambien las dependencias.

### 2. Terminal 1: arrancar el backend

Entra a la carpeta `Backend-MakiCore\backend` y ejecuta:

```powershell
uv sync
```

Configura la conexión a SQL Server en esta misma terminal:

```powershell
$env:DATABASE_URL = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\SQLEXPRESS;DATABASE=maki;Trusted_Connection=yes;TrustServerCertificate=yes;"
```

Lo único que cambia entre computadoras normalmente es `SERVER`:

- `localhost\SQLEXPRESS` si tienes SQL Server Express.
- `.` si utilizas la instancia por defecto (por ejemplo, en la PC del laboratorio).

Para saber cuál es el tuyo y qué otras partes pueden cambiar (driver o autenticación), revisa `Backend-MakiCore/backend/README.md`, sección "Cadena de conexión".

La base de datos y sus tablas se inicializan automáticamente al arrancar el backend con una conexión válida. No necesitas crearlas manualmente ni ejecutar el script SQL para iniciar el proyecto.

Arranca el backend:

```powershell
uv run uvicorn backend.main:app --reload --port 8000
```

Deja esta terminal abierta. Puedes verificar el funcionamiento desde el navegador:

- http://localhost:8000/salud
- http://localhost:8000/docs

### 3. Terminal 2: arrancar el frontend

Abre otra terminal en la carpeta raíz del proyecto y ejecuta:

```powershell
npm start
```

Entra a http://localhost:4200.

### 4. Usuarios de prueba

| Rol | Correo | Clave |
|---|---|---|
| Artesano | taller.godino@maki.pe | maki123 |
| Artesano | taller.palacios@maki.pe | maki123 |
| Comprador | comprador@maki.pe | maki123 |

### 5. Consultas SQL Server

Puedes ejecutar estas consultas desde SQL Server Management Studio (SSMS), seleccionando la base de datos `maki`.

**Ver todos los usuarios registrados:**

```sql
USE maki;
GO

SELECT id, correo, rol, artesano_id, nombre_publico, creado_en
FROM usuarios
ORDER BY id DESC;
```

**Buscar un usuario por correo:**

```sql
SELECT *
FROM usuarios
WHERE correo = 'prueba1@gmail.com';
```

**Ver el último usuario registrado:**

```sql
SELECT TOP 1 *
FROM usuarios
ORDER BY id DESC;
```

**Ver los artesanos registrados:**

```sql
SELECT *
FROM artesanos
ORDER BY artesano_id DESC;
```

**Ver las sesiones:**

```sql
SELECT usuario_id, creada_en, expira_en
FROM sesiones
ORDER BY creada_en DESC;
```

**Contar los usuarios registrados:**

```sql
SELECT COUNT(*) AS total_usuarios
FROM usuarios;
```

**Comprobar las contraseñas almacenadas:**

```sql
SELECT correo, clave_hash
FROM usuarios;
```

Las contraseñas se almacenan mediante hashes, no como texto legible.

### 6. Pruebas y compilación

En una tercera terminal, ejecuta los comandos correspondientes desde cada carpeta:

```powershell
npm test
npm run build
```

Los comandos anteriores corresponden al frontend y se ejecutan desde la raíz del proyecto.

Para las pruebas del backend, entra a `Backend-MakiCore\backend` y ejecuta:

```powershell
uv run pytest
```

Para detener cualquier servidor, presiona `Ctrl + C` en su terminal.

## Pantallas (rutas)

| Ruta | Qué muestra | Acceso |
|---|---|---|
| `/catalogo` | Catálogo con filtros por fibra (página inicial) | Público |
| `/carrito` | Carrito, zona de envío, total y división 20/80 | Público (pagar: comprador) |
| `/login` | Inicio y cierre de sesión | Público |
| `/artesano` | Registro de prendas (con foto y stock) y nuevas fibras | Solo artesano (`artesanoGuard`) |

Las rutas cargan de forma diferida y cualquier ruta desconocida lleva al catálogo.

## Estructura

```text
Backend-MakiCore/backend/   API FastAPI (repositorios, esquemas, seguridad, seed.py)
database-MakiCore/          Scripts SQL de la base de datos
src/app/
├── tienda.service.ts       Estado de la tienda: sesión, catálogo, carrito, moneda, envío y pedido
├── configuracion.ts        Valores de negocio: tasa EUR, tarifas de envío, 20/80, límites
├── dinero.ts               Funciones de dinero en centavos (conversión y división 20/80)
├── artesano.guard.ts       Protege /artesano
├── app.routes.ts           Rutas
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
- **Sin `DATABASE_URL` nada persiste.** Si no se configura la conexión, el backend guarda los datos en memoria y al reiniciarlo se pierden usuarios nuevos, prendas y pedidos. Con SQL Server conectado, los datos se conservan.
- Las fotos aceptan JPG, PNG o WebP de hasta 2 MB.
- Bootstrap, los iconos y las fuentes se cargan desde CDN (`src/index.html`).