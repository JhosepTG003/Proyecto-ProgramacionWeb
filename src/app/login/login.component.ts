import { Component, computed, inject, signal } from "@angular/core";
import { FormField, form, minLength, required, validate } from "@angular/forms/signals";
import { mensajeError } from "../api.service";
import { Rol, TiendaService } from "../tienda.service";

// Errores de tipeo frecuentes -> dominio correcto
const DOMINIOS_CORREGIDOS: Record<string, string> = {
  "gmial.com": "gmail.com",
  "gmai.com": "gmail.com",
  "gamil.com": "gmail.com",
  "gnail.com": "gmail.com",
  "gmail.co": "gmail.com",
  "gmail.con": "gmail.com",
  "gmail.cm": "gmail.com",
  "gmail.om": "gmail.com",
  "hotmial.com": "hotmail.com",
  "hotmal.com": "hotmail.com",
  "hotmail.con": "hotmail.com",
  "outlok.com": "outlook.com",
  "outlook.con": "outlook.com",
  "yaho.com": "yahoo.com",
  "yahoo.con": "yahoo.com",
};

// Dominio válido: etiquetas con letras/números/guiones (sin empezar ni terminar en guion) y extensión de 2+ letras.
const REGEX_DOMINIO = /^(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,}$/;
const REGEX_USUARIO = /^[A-Za-z0-9._%+-]+$/;

// Devuelve el mensaje de error, o "" si el correo es válido.
export function validarCorreo(valor: string): string {
  const correo = valor.trim();
  if (correo === "") return ""; // el "required" se encarga del vacío

  const arrobas = correo.split("@").length - 1;
  if (arrobas === 0) return "Falta el símbolo @ (ejemplo: nombre@gmail.com).";
  if (arrobas > 1) return "El correo solo puede tener un @.";

  const [usuario, dominio] = correo.split("@");
  if (usuario === "") return "Escribe tu usuario antes del @.";
  if (dominio === "") return "Escribe el dominio después del @ (ejemplo: gmail.com).";

  if (
    !REGEX_USUARIO.test(usuario) ||
    usuario.startsWith(".") ||
    usuario.endsWith(".") ||
    usuario.includes("..")
  ) {
    return "El usuario del correo tiene caracteres no válidos.";
  }

  const dominioMin = dominio.toLowerCase();
  const sugerido = DOMINIOS_CORREGIDOS[dominioMin];
  if (sugerido) return "¿Quisiste decir @" + sugerido + "?";

  if (!REGEX_DOMINIO.test(dominioMin)) {
    return "El dominio no es válido. Usa uno como gmail.com, hotmail.com u outlook.com.";
  }
  return "";
}

@Component({
  selector: "app-login",
  standalone: true,
  imports: [FormField],
  templateUrl: "./login.component.html",
})
export class LoginComponent {
  tienda = inject(TiendaService);

  // Signal Form: el modelo es un signal y las validaciones se declaran en el esquema.
  modelo = signal({ correo: "", clave: "" });
  formulario = form(this.modelo, (c) => {
    required(c.correo, { message: "Escribe tu correo electrónico." });
    validate(c.correo, ({ value }) => {
      const mensaje = validarCorreo(value());
      return mensaje ? { kind: "correo", message: mensaje } : null;
    });
    required(c.clave, { message: "Escribe tu contraseña." });
    minLength(c.clave, 6, {
      message: "La contraseña debe tener al menos 6 caracteres.",
    });
  });

  mensaje = signal("");
  esError = signal(false);
  verClave = signal(false);

  // Los errores se muestran cuando el usuario sale del campo (o intenta entrar).
  errorCorreo = computed(() => {
    const campo = this.formulario.correo();
    return campo.touched() ? (campo.errors()[0]?.message ?? "") : "";
  });
  errorClave = computed(() => {
    const campo = this.formulario.clave();
    return campo.touched() ? (campo.errors()[0]?.message ?? "") : "";
  });
  correoOk = computed(() => {
    const campo = this.formulario.correo();
    return campo.touched() && campo.errors().length === 0;
  });
  claveOk = computed(() => {
    const campo = this.formulario.clave();
    return campo.touched() && campo.errors().length === 0;
  });

  enviando = signal(false);

  // true si el formulario está bien; si no, muestra el primer error.
  private formularioValido(): boolean {
    this.formulario.correo().markAsTouched();
    this.formulario.clave().markAsTouched();

    if (this.formulario().invalid()) {
      this.esError.set(true);
      this.mensaje.set(this.formulario().errorSummary()[0]?.message ?? "Revisa los datos.");
      return false;
    }
    return true;
  }

  // El rol lo asigna el servidor según la cuenta: quien entra no lo elige.
  async ingresar() {
    if (this.enviando() || !this.formularioValido()) return;
    await this.enviar(async () => {
      const { correo, clave } = this.modelo();
      await this.tienda.ingresar(correo.trim().toLowerCase(), clave);
    });
  }

  // El rol se fija una sola vez, al crear la cuenta.
  async crearCuenta(rol: Rol) {
    if (this.enviando() || !this.formularioValido()) return;
    await this.enviar(async () => {
      const { correo, clave } = this.modelo();
      await this.tienda.crearCuenta(correo.trim().toLowerCase(), clave, rol);
    });
  }

  private async enviar(accion: () => Promise<void>) {
    this.enviando.set(true);
    try {
      await accion();
      this.esError.set(false);
      this.mensaje.set("Sesión iniciada como " + this.tienda.rol() + ".");
    } catch (e) {
      this.esError.set(true);
      this.mensaje.set(mensajeError(e));
    } finally {
      this.enviando.set(false);
    }
  }

  salir() {
    this.tienda.cerrarSesion();
    this.esError.set(false);
    this.mensaje.set("Sesión cerrada.");
  }
}
