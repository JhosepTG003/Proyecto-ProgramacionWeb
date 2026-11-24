# Maki Core

Tienda web de artesanías textiles del Valle del Mantaro, hecha con Angular y **Signals**
(`signal`, `computed`, `effect` y Signal Forms). Es un **prototipo de frontend**: todavía no
tiene backend ni base de datos.

## Cómo ejecutarlo

```bash
npm install
npm start        # ng serve -> http://localhost:4200
npm test         # pruebas unitarias (Vitest)
npm run build    # compilación de producción
```

## Pantallas (rutas)

| Ruta        | Qué muestra                                       | Acceso                      |
| ----------- | ------------------------------------------------- | --------------------------- |
| `/catalogo` | Catálogo con filtros por fibra (página inicial)   | Público                     |
| `/carrito`  | Carrito, zona de envío, total y división 20/80    | Público (pagar: comprador)  |
| `/login`    | Inicio y cierre de sesión                         | Público                     |
| `/artesano` | Registro de prendas (con foto) y nuevas fibras    | Solo artesano (`artesanoGuard`) |

Las rutas cargan de forma diferida y cualquier ruta desconocida lleva al catálogo.

## Estructura

```
src/app/
├── tienda.service.ts   Estado de la tienda: sesión, catálogo, carrito, moneda, envío y pedido
├── configuracion.ts    Valores de negocio: tasa EUR, tarifas de envío, 20/80, límites
├── dinero.ts           Funciones de dinero en centavos (conversión y división 20/80)
├── artesano.guard.ts   Protege /artesano
├── app.routes.ts       Rutas
└── catalogo/ carrito/ login/ artesano/   Un componente por pantalla
```

## Decisiones importantes

- **Dinero en centavos enteros.** Los precios y totales se guardan como enteros (`15000` = $150.00)
  para evitar errores de decimales. La división 20/80 siempre suma exactamente el subtotal.
- **Tipado estricto.** `strict` y `strictTemplates` activados; `Rol`, `Moneda`, `Zona` y
  `EstadoPedido` son uniones de texto, así que un error de escritura no compila.
- **El correo del artesano nunca se muestra.** El catálogo usa un nombre público
  (`Artesano ART-0003`), provisional hasta que exista el perfil con nombre del taller.
- **Un solo rol por sesión.** Para cambiar de rol hay que cerrar sesión (botón en el menú).

## Limitaciones del prototipo

- **El inicio de sesión es simulado.** El rol lo elige quien pulsa el botón y la contraseña solo
  valida el largo. El guard mejora la experiencia, pero la seguridad real debe venir de un backend
  que asigne el rol.
- **Nada persiste.** Al recargar se pierden sesión, carrito y prendas registradas. Las fotos se
  guardan en memoria (JPG, PNG o WebP de hasta 2 MB).
- Bootstrap, los iconos y las fuentes se cargan desde CDN (`src/index.html`).

## Pendiente

- Backend y base de datos (sesión, roles, prendas, pedidos).
- Perfil del artesano con nombre del taller.
- Instalar Bootstrap e iconos con npm en lugar de CDN.
