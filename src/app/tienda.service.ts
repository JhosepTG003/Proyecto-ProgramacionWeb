import { Injectable, computed, signal } from "@angular/core";
import { form } from "@angular/forms/signals";
import {
  MAX_CANTIDAD_POR_PRENDA,
  TARIFAS_ENVIO_CENTAVOS_USD,
} from "./configuracion";
import { convertir, dividirVenta } from "./dinero";

// ---------- Tipos ----------
// Uniones de texto en vez de string suelto: si alguien escribe "Aprobdo" el compilador lo avisa.
export type Rol = "comprador" | "artesano";
export type Moneda = "USD" | "EUR";
export type Zona = "America" | "Europa" | "Otros";
export type EstadoPedido = "Sin pedido" | "Aprobado";

// ---------- Modelos ----------
// Todos los montos son enteros en CENTAVOS (ver configuracion.ts).
export interface Prenda {
  id: string;
  nombre: string;
  artesano: string;
  artesanoId: string; // ID único del artesano (ej. ART-0003)
  fibra: string;
  tinte: string;
  precioCentavosUSD: number; // precio base en centavos de USD
  foto?: string; // data URL de la fotografía (opcional)
}

export type NuevaPrenda = Omit<Prenda, "id">;

export interface LineaCarrito {
  prenda: Prenda;
  cantidad: number;
  precio: number; // precio unitario en centavos de la moneda mostrada
  subtotal: number; // en centavos de la moneda mostrada
}

@Injectable({ providedIn: "root" })
export class TiendaService {
  // ---------- Sesión (RF002, RF003) ----------
  usuario = signal("");
  rol = signal<Rol | null>(null);
  estaLogueado = computed(() => this.rol() !== null);

  // ---------- ID único de artesano ----------
  // Mapa correo -> ID. Si el mismo correo vuelve a entrar recibe siempre el mismo ID.
  artesanos = signal<Record<string, string>>({
    "Taller Godiño Yanqui": "ART-0001",
    "Taller Palacios Yalico": "ART-0002",
  });
  idArtesano = signal(""); // ID del artesano con sesión iniciada

  // Nombre público del artesano: es lo que ve el catálogo. NUNCA se usa el correo (dato privado).
  // Provisional: "Artesano ART-0003". Cuando exista un perfil con nombre del taller, sale de ahí.
  nombreArtesano = computed(() => (this.idArtesano() === "" ? "" : "Artesano " + this.idArtesano()));

  // ---------- Catálogo (RF004): lista viva de prendas ----------
  // Cuando un artesano registra una prenda se agrega aquí y el catálogo se actualiza solo.
  prendas = signal<Prenda[]>([
    {
      id: "poncho-andino",
      nombre: "Poncho Andino Tradicional",
      artesano: "Taller Godiño Yanqui",
      artesanoId: "ART-0001",
      fibra: "Alpaca",
      tinte: "Nogal (Marrón natural)",
      precioCentavosUSD: 15000,
    },
    {
      id: "chalina-hualhuas",
      nombre: "Chalina Hualhuas",
      artesano: "Taller Palacios Yalico",
      artesanoId: "ART-0002",
      fibra: "Lana ovina",
      tinte: "Cochinilla (Rojo carmín)",
      precioCentavosUSD: 4500,
    },
  ]);

  // ---------- Fibras: lista viva ----------
  // El artesano puede agregar nuevas fibras; el formulario y los filtros del catálogo se actualizan solos.
  fibras = signal<string[]>(["Alpaca", "Llama", "Lana ovina"]);

  // ---------- Aviso emergente (toast) ----------
  aviso = signal("");
  private temporizadorAviso: ReturnType<typeof setTimeout> | undefined;

  // ---------- Moneda (RNF010) ----------
  moneda = signal<Moneda>("USD");
  simbolo = computed(() => (this.moneda() === "EUR" ? "€" : "$"));

  // ---------- Envío (RF010): zona manejada con Signal Forms ----------
  modeloEnvio = signal<{ zona: Zona }>({ zona: "America" });
  formEnvio = form(this.modeloEnvio);
  zona = computed(() => this.modeloEnvio().zona);

  // ---------- Carrito: cantidad por id de prenda ----------
  cantidades = signal<Record<string, number>>({});

  lineas = computed<LineaCarrito[]>(() => {
    const cant = this.cantidades();
    const moneda = this.moneda();
    return this.prendas()
      .filter((p) => (cant[p.id] ?? 0) > 0)
      .map((p) => {
        const cantidad = cant[p.id];
        const precio = convertir(p.precioCentavosUSD, moneda);
        return { prenda: p, cantidad, precio, subtotal: cantidad * precio };
      });
  });

  totalPrendas = computed(() => this.lineas().reduce((n, l) => n + l.cantidad, 0));
  subtotal = computed(() => this.lineas().reduce((s, l) => s + l.subtotal, 0));

  // Envío fijo por zona (la tarifa está en USD y se convierte a la moneda mostrada).
  envio = computed(() =>
    this.subtotal() === 0 ? 0 : convertir(TARIFAS_ENVIO_CENTAVOS_USD[this.zona()], this.moneda()),
  );

  total = computed(() => this.subtotal() + this.envio());

  // ---------- División 20/80 (RF021) ----------
  // Se reparte el subtotal; el envío no entra en la división.
  private division = computed(() => dividirVenta(this.subtotal()));
  plataforma = computed(() => this.division().plataforma);
  cooperativa = computed(() => this.division().cooperativa);

  // ---------- Pedido ----------
  estadoPedido = signal<EstadoPedido>("Sin pedido");
  mensajePedido = signal("");

  // ---------- Artesano (RF004, RF016) ----------
  prendasRegistradas = signal(0);
  ultimaPrenda = signal("");
  ultimoQR = signal("");

  // ---------- Precio mostrado de una prenda en la moneda actual (en centavos) ----------
  precioMostrado(p: Prenda): number {
    return convertir(p.precioCentavosUSD, this.moneda());
  }

  // Da formato a un monto en centavos con el símbolo de la moneda actual: 7360 -> "€73.60".
  mostrar(centavos: number): string {
    return this.simbolo() + (centavos / 100).toFixed(2);
  }

  // ---------- Moneda ----------
  cambiarMoneda(moneda: Moneda) {
    this.moneda.set(moneda);
  }

  // ---------- Carrito ----------
  readonly maxPorPrenda = MAX_CANTIDAD_POR_PRENDA;

  enCarrito(id: string): number {
    return this.cantidades()[id] ?? 0;
  }

  // Devuelve true si se añadió. El aviso emergente solo sale cuando conAviso es true
  // (el catálogo lo usa; los botones "+" del carrito no, porque ya ven el cambio).
  agregar(id: string, conAviso = true): boolean {
    const prenda = this.prendas().find((p) => p.id === id);
    if (!prenda) return false;
    if (this.enCarrito(id) >= this.maxPorPrenda) {
      this.avisar("Máximo " + this.maxPorPrenda + " unidades de " + prenda.nombre);
      return false;
    }
    this.cantidades.update((c) => ({ ...c, [id]: (c[id] ?? 0) + 1 }));
    if (conAviso) this.avisar(prenda.nombre + " se añadió al carrito");
    return true;
  }

  avisar(texto: string) {
    this.aviso.set(texto);
    clearTimeout(this.temporizadorAviso);
    this.temporizadorAviso = setTimeout(() => this.aviso.set(""), 2200);
  }

  quitar(id: string) {
    this.cantidades.update((c) => {
      const actual = c[id] ?? 0;
      if (actual <= 1) {
        const { [id]: _, ...resto } = c;
        return resto;
      }
      return { ...c, [id]: actual - 1 };
    });
  }

  // ---------- Nuevas fibras (artesano) ----------
  // Devuelve ok=true y la fibra normalizada (o la ya existente si estaba repetida).
  agregarFibra(texto: string): { ok: boolean; mensaje: string; fibra: string } {
    const limpio = texto.trim().replace(/\s+/g, " ");
    if (limpio.length < 3) {
      return { ok: false, mensaje: "Escribe al menos 3 letras.", fibra: "" };
    }
    if (limpio.length > 30) {
      return { ok: false, mensaje: "Máximo 30 caracteres.", fibra: "" };
    }
    if (!/^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:[ -][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*$/.test(limpio)) {
      return { ok: false, mensaje: "Usa solo letras (sin números ni símbolos).", fibra: "" };
    }

    // Formato uniforme: "vicuña" / "VICUÑA" -> "Vicuña"
    const minus = limpio.toLowerCase();
    const normalizada = minus.charAt(0).toUpperCase() + minus.slice(1);

    // Evita duplicados sin importar mayúsculas ni tildes
    const clave = (t: string) =>
      t.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
    const existente = this.fibras().find((f) => clave(f) === clave(normalizada));
    if (existente) {
      return { ok: false, mensaje: "Esa fibra ya existe: \"" + existente + "\".", fibra: existente };
    }

    this.fibras.update((lista) => [...lista, normalizada]);
    return { ok: true, mensaje: "", fibra: normalizada };
  }

  // ---------- Registro de prendas (artesano) ----------
  registrarPrenda(datos: NuevaPrenda): Prenda {
    const numero = this.prendasRegistradas() + 1;
    // Código único de la prenda (aquí se generaría el QR)
    const codigo = "MAKI-" + String(numero).padStart(4, "0");
    const prenda: Prenda = { id: codigo, ...datos };

    // Por seguridad: si la fibra no estaba en la lista, se agrega.
    if (!this.fibras().includes(datos.fibra)) {
      this.fibras.update((lista) => [...lista, datos.fibra]);
    }

    this.prendas.update((lista) => [...lista, prenda]);
    this.prendasRegistradas.set(numero);
    this.ultimaPrenda.set(prenda.nombre);
    this.ultimoQR.set(codigo);
    return prenda;
  }

  // ---------- Sesión ----------
  iniciarSesion(correo: string, rol: Rol) {
    this.usuario.set(correo);
    this.rol.set(rol);
    this.idArtesano.set(rol === "artesano" ? this.obtenerIdArtesano(correo) : "");
  }

  // Devuelve el ID del artesano; si es nuevo, genera el siguiente (ART-0003, ART-0004...).
  private obtenerIdArtesano(correo: string): string {
    const existente = this.artesanos()[correo];
    if (existente) return existente;

    const numero = Object.keys(this.artesanos()).length + 1;
    const id = "ART-" + String(numero).padStart(4, "0");
    this.artesanos.update((mapa) => ({ ...mapa, [correo]: id }));
    return id;
  }

  cerrarSesion() {
    this.idArtesano.set("");
    this.usuario.set("");
    this.rol.set(null);
  }

  // ---------- Pedido ----------
  pagar() {
    if (this.totalPrendas() === 0) {
      this.mensajePedido.set("El carrito está vacío.");
      return;
    }
    if (this.rol() !== "comprador") {
      this.mensajePedido.set("Debes iniciar sesión como comprador para pagar.");
      return;
    }
    this.estadoPedido.set("Aprobado");
    this.mensajePedido.set(
      "Pago aprobado. Se notificó la venta al artesano y se ordenó la transferencia del 80 % a la cooperativa.",
    );
  }

  nuevoPedido() {
    this.cantidades.set({});
    this.estadoPedido.set("Sin pedido");
    this.mensajePedido.set("");
  }
}
