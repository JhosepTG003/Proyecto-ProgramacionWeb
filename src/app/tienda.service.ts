import { Injectable, computed, signal } from "@angular/core";
import { form } from "@angular/forms/signals";

// ---------- Modelos ----------
export interface Prenda {
  id: string;
  nombre: string;
  artesano: string;
  fibra: string;
  tinte: string;
  precioUSD: number; // precio base en USD
}

export interface NuevaPrenda {
  nombre: string;
  artesano: string;
  fibra: string;
  tinte: string;
  precioUSD: number;
}

export interface LineaCarrito {
  prenda: Prenda;
  cantidad: number;
  precio: number; // precio unitario en la moneda mostrada
  subtotal: number;
}

@Injectable({ providedIn: "root" })
export class TiendaService {
  // ---------- Sesión (RF002, RF003) ----------
  usuario = signal("");
  rol = signal("");
  estaLogueado = signal(false);

  // ---------- Catálogo (RF004): lista viva de prendas ----------
  // Cuando un artesano registra una prenda se agrega aquí y el catálogo se actualiza solo.
  prendas = signal<Prenda[]>([
    {
      id: "poncho-andino",
      nombre: "Poncho Andino Tradicional",
      artesano: "Taller Godiño Yanqui",
      fibra: "Alpaca",
      tinte: "Nogal (Marrón natural)",
      precioUSD: 150,
    },
    {
      id: "chalina-hualhuas",
      nombre: "Chalina Hualhuas",
      artesano: "Taller Palacios Yalico",
      fibra: "Lana de Ovino",
      tinte: "Cochinilla (Rojo carmín)",
      precioUSD: 45,
    },
  ]);

  // ---------- Fibras: lista viva ----------
  // El artesano puede agregar nuevas fibras; el formulario y los filtros del catálogo se actualizan solos.
  fibras = signal<string[]>(["Alpaca", "Llama", "Lana de Ovino"]);

  // ---------- Aviso emergente (toast) ----------
  aviso = signal("");
  private temporizadorAviso: ReturnType<typeof setTimeout> | undefined;

  // ---------- Moneda (RNF010) ----------
  tasaEUR = 0.92;
  moneda = signal("USD");
  simbolo = computed(() => (this.moneda() === "EUR" ? "€" : "$"));
  factor = computed(() => (this.moneda() === "EUR" ? this.tasaEUR : 1));

  // ---------- Envío (RF010): zona manejada con Signal Forms ----------
  modeloEnvio = signal({ zona: "America" });
  formEnvio = form(this.modeloEnvio);
  zona = computed(() => this.modeloEnvio().zona);

  // ---------- Carrito: cantidad por id de prenda ----------
  cantidades = signal<Record<string, number>>({});

  lineas = computed<LineaCarrito[]>(() => {
    const cant = this.cantidades();
    const factor = this.factor();
    return this.prendas()
      .filter((p) => (cant[p.id] ?? 0) > 0)
      .map((p) => {
        const cantidad = cant[p.id];
        const precio = p.precioUSD * factor;
        return { prenda: p, cantidad, precio, subtotal: cantidad * precio };
      });
  });

  totalPrendas = computed(() => this.lineas().reduce((n, l) => n + l.cantidad, 0));
  subtotal = computed(() => this.lineas().reduce((s, l) => s + l.subtotal, 0));

  envio = computed(() => {
    if (this.subtotal() === 0) return 0;
    // Envío fijo por zona (en USD, luego se convierte)
    let tarifaUSD = 40;
    if (this.zona() === "America") tarifaUSD = 25;
    if (this.zona() === "Europa") tarifaUSD = 30;
    return tarifaUSD * this.factor();
  });

  total = computed(() => this.subtotal() + this.envio());

  // ---------- División 20/80 (RF021) ----------
  plataforma = computed(() => this.subtotal() * 0.2);
  cooperativa = computed(() => this.subtotal() * 0.8);

  // ---------- Pedido ----------
  estadoPedido = signal("Sin pedido");
  mensajePedido = signal("");

  // ---------- Artesano (RF004, RF016) ----------
  prendasRegistradas = signal(0);
  ultimaPrenda = signal("");
  ultimoQR = signal("");

  // ---------- Precio mostrado de una prenda en la moneda actual ----------
  precioMostrado(p: Prenda): number {
    return p.precioUSD * this.factor();
  }

  // ---------- Moneda ----------
  cambiarMoneda(moneda: string) {
    this.moneda.set(moneda);
  }

  // ---------- Carrito ----------
  agregar(id: string) {
    this.cantidades.update((c) => ({ ...c, [id]: (c[id] ?? 0) + 1 }));
    const prenda = this.prendas().find((p) => p.id === id);
    if (prenda) this.avisar(prenda.nombre + " se añadió al carrito");
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
  iniciarSesion(correo: string, rol: string) {
    this.usuario.set(correo);
    this.rol.set(rol);
    this.estaLogueado.set(true);
  }

  cerrarSesion() {
    this.usuario.set("");
    this.rol.set("");
    this.estaLogueado.set(false);
  }

  // ---------- Pedido ----------
  pagar() {
    if (this.totalPrendas() === 0) {
      this.mensajePedido.set("El carrito está vacío.");
      return;
    }
    if (!this.estaLogueado() || this.rol() !== "comprador") {
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
