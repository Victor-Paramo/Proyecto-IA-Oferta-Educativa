"""Cliente gráfico del asistente de oferta educativa.

Utiliza MotorEducativo directamente, sin subprocesos ni lectura de PowerShell.
La inicialización y las consultas se realizan en un hilo de trabajo; los widgets
solo se actualizan desde el hilo principal de Tkinter.
"""

import queue
import threading
from tkinter import messagebox

import customtkinter as ctk

from app import MotorEducativo

try:
    import keyring
except ImportError:
    keyring = None


SERVICIO_CREDENCIALES = "Oferta Educativa CDMX 2.0"
CUENTA_CREDENCIALES = "postgresql_local"


class InterfazEducativa(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        super().__init__()
        self.title("Oferta Educativa Ciudad de México 2.0")
        self.geometry("1050x680")
        self.minsize(800, 500)

        self.motor = None
        self.eventos = queue.Queue()
        self.solicitudes = queue.Queue()
        self.en_proceso = False
        self.cerrando = False

        ctk.CTkLabel(self, text="Oferta Educativa CDMX 2.0",
                     font=ctk.CTkFont(size=26, weight="bold")).pack(pady=(25, 6))
        ctk.CTkLabel(self, text="Asistente inteligente de consulta académica",
                     font=ctk.CTkFont(size=15)).pack(pady=(0, 12))

        self.historial = ctk.CTkTextbox(self, wrap="word")
        self.historial.pack(fill="both", expand=True, padx=25, pady=10)
        self.historial.configure(state="disabled")

        self.estado = ctk.CTkLabel(self, text="Preparando el motor de IA...", anchor="w")
        self.estado.pack(fill="x", padx=25)
        self.entrada = ctk.CTkEntry(self, placeholder_text="Escribe tu pregunta...")
        self.entrada.pack(fill="x", padx=25, pady=(8, 5))
        self.entrada.bind("<Return>", self.enviar)
        self.boton = ctk.CTkButton(self, text="Enviar", command=self.enviar)
        self.boton.pack(pady=(3, 12))
        self._habilitar(False)

        ctk.CTkLabel(self,
                     text="Fuente: registros SEP del 30 de abril de 2021; vigencia no verificada.",
                     font=ctk.CTkFont(size=11)).pack(pady=(0, 9))
        self.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.after(100, self._procesar_eventos)
        self.after(200, self._iniciar)

    def _mostrar(self, texto):
        if not texto.strip():
            return
        self.historial.configure(state="normal")
        self.historial.insert("end", texto.strip() + "\n\n")
        self.historial.configure(state="disabled")
        self.historial.see("end")

    def _habilitar(self, habilitado):
        estado = "normal" if habilitado else "disabled"
        self.entrada.configure(state=estado)
        self.boton.configure(state=estado)
        if habilitado:
            self.entrada.focus_set()

    def _obtener_contrasena(self):
        if keyring is None:
            messagebox.showerror("Dependencia necesaria", "Se requiere keyring: python -m pip install keyring")
            return None
        try:
            contrasena = keyring.get_password(SERVICIO_CREDENCIALES, CUENTA_CREDENCIALES)
        except Exception as exc:
            messagebox.showerror("Credenciales", f"No se pudo leer el almacén de Windows: {exc}")
            return None
        if contrasena:
            return contrasena
        dialogo = ctk.CTkInputDialog(
            text="Contraseña local de PostgreSQL (se guardará en Windows):",
            title="Conexión a PostgreSQL",
        )
        contrasena = dialogo.get_input()
        if not contrasena:
            return None
        try:
            keyring.set_password(SERVICIO_CREDENCIALES, CUENTA_CREDENCIALES, contrasena)
        except Exception as exc:
            messagebox.showerror("Credenciales", f"No se pudo guardar la contraseña: {exc}")
            return None
        return contrasena

    def _iniciar(self):
        contrasena = self._obtener_contrasena()
        if contrasena is None:
            self.estado.configure(text="Conexión cancelada")
            return
        self.estado.configure(text="Inicializando PostgreSQL, clasificador y MiniLM...")
        threading.Thread(target=self._trabajar, args=(contrasena,), daemon=True).start()

    def _trabajar(self, contrasena):
        """Toda la sesión usa el mismo hilo y la misma conexión PostgreSQL."""
        try:
            self.motor = MotorEducativo(contrasena=contrasena)
            self.eventos.put(("listo", None))
            while True:
                pregunta = self.solicitudes.get()
                if pregunta is None:
                    break
                try:
                    resultado = self.motor.procesar(pregunta)
                    self.eventos.put(("respuesta", resultado))
                    if resultado["cerrar"]:
                        break
                except Exception as exc:
                    self.eventos.put(("error_consulta", str(exc)))
        except Exception as exc:
            self.eventos.put(("error_inicio", str(exc)))
        finally:
            if self.motor is not None:
                self.motor.cerrar()
            self.eventos.put(("finalizado", None))

    def _procesar_eventos(self):
        if self.cerrando:
            return
        try:
            while True:
                tipo, valor = self.eventos.get_nowait()
                if tipo == "listo":
                    self.en_proceso = False
                    self.estado.configure(text="Motor listo para consultas")
                    self._habilitar(True)
                elif tipo == "respuesta":
                    if valor["mensaje"]:
                        self._mostrar("Asistente:\n" + valor["mensaje"])
                    self.en_proceso = False
                    if valor["cerrar"]:
                        self.estado.configure(text="Sesión finalizada")
                        self._habilitar(False)
                    else:
                        self.estado.configure(text="Motor listo para consultas")
                        self._habilitar(True)
                elif tipo == "error_consulta":
                    self._mostrar("Error al procesar la consulta: " + valor)
                    self.en_proceso = False
                    self.estado.configure(text="Motor listo para consultas")
                    self._habilitar(True)
                elif tipo == "error_inicio":
                    self._mostrar("No se pudo iniciar el motor: " + valor)
                    self.estado.configure(text="Error de inicialización")
                elif tipo == "finalizado":
                    self._habilitar(False)
                    if not self.estado.cget("text").startswith("Error"):
                        self.estado.configure(text="Sesión finalizada")
        except queue.Empty:
            pass
        self.after(100, self._procesar_eventos)

    def enviar(self, _evento=None):
        if self.en_proceso or self.motor is None:
            return
        pregunta = self.entrada.get().strip()
        if not pregunta:
            return
        self.entrada.delete(0, "end")
        self._mostrar("Estudiante: " + pregunta)
        self.en_proceso = True
        self._habilitar(False)
        self.estado.configure(text="Procesando consulta...")
        self.solicitudes.put(pregunta)

    def cerrar(self):
        self.cerrando = True
        self.solicitudes.put(None)
        # No se espera al hilo para evitar congelar la ventana al cerrar.
        self.destroy()


if __name__ == "__main__":
    InterfazEducativa().mainloop()
