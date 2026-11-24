import { Component, inject, signal } from "@angular/core";
import { FormField, form, required, validate } from "@angular/forms/signals";
import { MAX_FOTO_BYTES, MAX_PRECIO_USD, TIPOS_FOTO } from "../configuracion";
import { usdACentavos } from "../dinero";
import { TiendaService } from "../tienda.service";

const FORMULARIO_VACIO = { nombre: "", fibra: "Alpaca", tinte: "", precio: 0 };
const OPCION_NUEVA = "__nueva__";

@Component({
  selector: "app-artesano",
  standalone: true,
  imports: [FormField],
  templateUrl: "./artesano.component.html",
})
export class ArtesanoComponent {
  tienda = inject(TiendaService);
  readonly OPCION_NUEVA = OPCION_NUEVA;

  // Signal Form: el modelo es un signal y las validaciones se declaran en el esquema.
  modelo = signal({ ...FORMULARIO_VACIO });
  formulario = form(this.modelo, (c) => {
    required(c.nombre);
    required(c.tinte);
    validate(c.precio, ({ value }) => {
      const precio = value();
      if (!(precio > 0)) return { kind: "precio", message: "El precio debe ser mayor a 0." };
      if (precio > MAX_PRECIO_USD) {
        return { kind: "precio", message: "El precio máximo es $" + MAX_PRECIO_USD + "." };
      }
      return null;
    });
  });

  mensaje = signal("");
  esError = signal(false);

  // ---------- Fotografía (opcional) ----------
  // Se guarda como data URL en memoria. Con backend se subiría a un servidor de archivos.
  foto = signal("");
  errorFoto = signal("");
  readonly tiposFoto = TIPOS_FOTO.join(",");

  elegirFoto(evento: Event) {
    const campo = evento.target as HTMLInputElement;
    const archivo = campo.files?.[0];
    this.foto.set("");
    this.errorFoto.set("");
    if (!archivo) return;

    if (!(TIPOS_FOTO as readonly string[]).includes(archivo.type)) {
      this.errorFoto.set("Usa una imagen JPG, PNG o WebP.");
      campo.value = "";
      return;
    }
    if (archivo.size > MAX_FOTO_BYTES) {
      this.errorFoto.set("La imagen pesa más de " + MAX_FOTO_BYTES / (1024 * 1024) + " MB.");
      campo.value = "";
      return;
    }

    const lector = new FileReader();
    lector.onload = () => this.foto.set(typeof lector.result === "string" ? lector.result : "");
    lector.onerror = () => this.errorFoto.set("No se pudo leer la imagen.");
    lector.readAsDataURL(archivo);
  }

  // ---------- Nueva fibra ----------
  agregandoFibra = signal(false);
  fibraNueva = signal("");
  errorFibra = signal("");

  elegirFibra(valor: string) {
    if (valor === OPCION_NUEVA) {
      this.agregandoFibra.set(true);
      return;
    }
    this.agregandoFibra.set(false);
    this.errorFibra.set("");
    this.modelo.update((m) => ({ ...m, fibra: valor }));
  }

  guardarFibra() {
    if (this.tienda.rol() !== "artesano") {
      this.errorFibra.set("Debes iniciar sesión como artesano.");
      return;
    }
    const resultado = this.tienda.agregarFibra(this.fibraNueva());
    if (!resultado.ok) {
      this.errorFibra.set(resultado.mensaje);
      // Si ya existía, la dejamos seleccionada para ayudar al usuario.
      if (resultado.fibra !== "") {
        this.modelo.update((m) => ({ ...m, fibra: resultado.fibra }));
      }
      return;
    }
    // La fibra ya está en TiendaService.fibras: el select y los filtros del catálogo se actualizan solos.
    this.modelo.update((m) => ({ ...m, fibra: resultado.fibra }));
    this.agregandoFibra.set(false);
    this.fibraNueva.set("");
    this.errorFibra.set("");
    this.esError.set(false);
    this.mensaje.set('Fibra "' + resultado.fibra + '" agregada al catálogo.');
  }

  cancelarFibra() {
    this.agregandoFibra.set(false);
    this.fibraNueva.set("");
    this.errorFibra.set("");
  }

  // ---------- Registro de prenda ----------
  registrar(campoFoto?: HTMLInputElement) {
    this.esError.set(true);

    if (this.tienda.rol() !== "artesano") {
      this.mensaje.set("Debes iniciar sesión como artesano.");
      return;
    }
    if (this.agregandoFibra()) {
      this.mensaje.set("Termina de agregar la nueva fibra o cancela para continuar.");
      return;
    }

    if (this.errorFoto() !== "") {
      this.mensaje.set("Corrige la fotografía o quítala para continuar.");
      return;
    }

    const datos = this.modelo();
    const nombre = datos.nombre.trim();
    const tinte = datos.tinte.trim();
    if (this.formulario().invalid() || nombre === "" || tinte === "") {
      this.mensaje.set("Completa todos los campos.");
      return;
    }

    // La prenda entra al catálogo (TiendaService.prendas) y se muestra de inmediato.
    this.tienda.registrarPrenda({
      nombre,
      artesano: this.tienda.nombreArtesano(), // nombre público, no el correo
      artesanoId: this.tienda.idArtesano(),
      fibra: datos.fibra,
      tinte,
      precioCentavosUSD: usdACentavos(datos.precio),
      foto: this.foto() || undefined,
    });

    this.esError.set(false);
    this.mensaje.set("Prenda registrada correctamente. Ya aparece en el catálogo.");
    this.formulario().reset({ ...FORMULARIO_VACIO });
    this.foto.set("");
    this.errorFoto.set("");
    if (campoFoto) campoFoto.value = "";
  }
}
