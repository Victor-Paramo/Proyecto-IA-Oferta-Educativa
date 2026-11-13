
import queue
import re
import threading
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from app import MotorEducativo

try:
    import keyring
except ImportError:
    keyring = None


SERVICIO_CREDENCIALES = "Oferta Educativa CDMX 2.0"
CUENTA_CREDENCIALES = "postgresql_local"

COLORES = {
    "fondo": "#F5F6F8",
    "barra": "#D8DDE4",
    "blanco": "#FFFFFF",
    "borde": "#AAB3C0",
    "principal": "#252C38",
    "principal_hover": "#37465B",
    "mensaje_usuario": "#DCE5E6",
    "tarjeta": "#E3E6EB",
    "texto": "#101418",
    "muted": "#252C35",
    "exito": "#183D54",
}


class InterfazEducativa(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        super().__init__(fg_color=COLORES["fondo"])
        self.title("Oferta Educativa Ciudad de México 2.0")
        self.geometry("1080x690")
        self.minsize(900, 580)
        self._aplicar_opacidad(1.0)
        self._cargar_logo()

        self.motor = None
        self.eventos = queue.Queue()
        self.solicitudes = queue.Queue()
        self.en_proceso = False
        self.cerrando = False
        self.mensajes = 0
        self._botones_afinidades = []
        self._confirmacion_afinidades = None
        self._rueda_acumulada = 0

        self._construir_interfaz()
        self._habilitar(False)
        self.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.after(100, self._procesar_eventos)
        self.after(200, self._iniciar)

    def _cargar_logo(self):
        """Carga el birrete para el encabezado y la barra de titulo."""
        from pathlib import Path
        ruta_logo = Path(__file__).resolve().parent / "recursos" / "logo_oferta_educativa.png"
        original = tk.PhotoImage(file=str(ruta_logo))
        self._logo_encabezado = original.subsample(13, 13)
        self._logo_ventana = original.subsample(16, 16)
        self.iconphoto(True, self._logo_ventana)

    def _aplicar_opacidad(self, valor):
        """Transparencia general, limitada para mantener legibles los textos."""
        try:
            self.attributes("-alpha", float(valor))
        except Exception:
            pass

    def _construir_interfaz(self):
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)


        cabecera = ctk.CTkFrame(self, height=65, fg_color=COLORES["principal"],
                                corner_radius=12)
        cabecera.grid(row=0, column=0, sticky="ew", padx=12, pady=(11, 4))
        cabecera.grid_propagate(False)
        cabecera.grid_columnconfigure(0, weight=0)
        cabecera.grid_columnconfigure(1, weight=1)
        tk.Label(cabecera, image=self._logo_encabezado,
                 bg=COLORES["principal"], bd=0,
                 highlightthickness=0).grid(
                     row=0, column=0, padx=(18, 0), pady=8)
        ctk.CTkLabel(cabecera, text="Oferta Educativa CDMX 2.0",
                     text_color="#FFFFFF", fg_color="transparent",
                     font=ctk.CTkFont(size=21, weight="bold"),
                     anchor="w").grid(row=0, column=1, sticky="ew",
                                      padx=(12, 20), pady=15)

        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.grid(row=1, column=0, sticky="nsew", padx=12, pady=(4, 12))
        cuerpo.grid_rowconfigure(0, weight=1)
        cuerpo.grid_columnconfigure(1, weight=1)

        lateral = ctk.CTkFrame(cuerpo, width=224, corner_radius=13,
                               fg_color=COLORES["barra"])
        lateral.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        lateral.grid_propagate(False)
        lateral.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(lateral, text="CONSULTAS", anchor="w",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=COLORES["texto"]).grid(
                         row=0, column=0, sticky="ew", padx=16, pady=(20, 12))
        ejemplos = [
            ("Buscar una carrera", "¿Dónde puedo estudiar Psicología?"),
            ("Explorar intereses", "Me interesa algo relacionado con robótica."),
            ("Buscar universidad", "¿Qué carreras ofrece la Universidad ICEL?"),
        ]
        for i, (texto, consulta) in enumerate(ejemplos, start=1):
            ctk.CTkButton(lateral, text=texto, anchor="w", height=43,
                          font=ctk.CTkFont(size=14),
                          fg_color="#F3F5F7", hover_color="#C5CED9",
                          text_color=COLORES["texto"], corner_radius=9,
                          command=lambda p=consulta: self._ejemplo(p)).grid(
                              row=i, column=0, sticky="ew", padx=12, pady=5)
        lateral.grid_rowconfigure(5, weight=1)
        self.nueva = ctk.CTkButton(
            lateral, text="+  Nueva conversación", height=43,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORES["principal"], hover_color=COLORES["principal_hover"],
            corner_radius=9, command=self.nueva_conversacion)
        self.nueva.grid(row=6, column=0, sticky="ew", padx=12, pady=(0, 16))
        ctk.CTkLabel(lateral, text="Catálogo SEP · abril de 2021",
                     font=ctk.CTkFont(size=12), text_color=COLORES["texto"]
                     ).grid(row=7, column=0, pady=(0, 15))

        principal = ctk.CTkFrame(cuerpo, fg_color="transparent")
        principal.grid(row=0, column=1, sticky="nsew")
        principal.grid_columnconfigure(0, weight=1)
        principal.grid_rowconfigure(1, weight=1)

        marco_historial = ctk.CTkFrame(
            principal, fg_color=COLORES["blanco"], corner_radius=13,
            border_width=1, border_color=COLORES["borde"])
        marco_historial.grid(row=1, column=0, sticky="nsew")
        marco_historial.grid_rowconfigure(0, weight=1)
        marco_historial.grid_columnconfigure(0, weight=1)

        self.lienzo_historial = tk.Canvas(
            marco_historial, bg=COLORES["blanco"], bd=0,
            relief="flat", highlightthickness=0, yscrollincrement=17)
        self.lienzo_historial.grid(row=0, column=0, sticky="nsew",
                                  padx=(10, 0), pady=10)
        self.scrollbar_historial = tk.Scrollbar(
            marco_historial, orient="vertical", width=13,
            command=self.lienzo_historial.yview,
            bg=COLORES["borde"], troughcolor=COLORES["blanco"],
            activebackground=COLORES["principal"])
        self.scrollbar_historial.grid(row=0, column=1, sticky="ns",
                                     padx=(0, 7), pady=10)
        self.lienzo_historial.configure(yscrollcommand=self.scrollbar_historial.set)
        self.historial = ctk.CTkFrame(
            self.lienzo_historial, corner_radius=0,
            fg_color=COLORES["blanco"])
        self.historial.grid_columnconfigure(0, weight=1)
        self._historial_ventana = self.lienzo_historial.create_window(
            (0, 0), window=self.historial, anchor="nw")
        self.historial.bind("<Configure>", self._actualizar_region_historial, add="+")
        self.lienzo_historial.bind("<Configure>", self._ajustar_ancho_historial, add="+")

        self.bind_all("<MouseWheel>", self._desplazar_historial, add="+")
        self.bind_all("<Button-4>", self._desplazar_historial, add="+")
        self.bind_all("<Button-5>", self._desplazar_historial, add="+")
        self._etiquetas_adaptables = []

        inferior = ctk.CTkFrame(principal, fg_color=COLORES["blanco"],
                                corner_radius=12, border_width=1,
                                border_color=COLORES["borde"])
        inferior.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        inferior.grid_columnconfigure(0, weight=1)
        self.estado = ctk.CTkLabel(inferior, text="Preparando motor de IA...",
                                   text_color=COLORES["exito"],
                                   font=ctk.CTkFont(size=13), anchor="w")
        self.estado.grid(row=0, column=0, columnspan=2, sticky="ew",
                         padx=13, pady=(9, 3))
        self.entrada = ctk.CTkEntry(
            inferior, height=47, corner_radius=9, border_color=COLORES["borde"],
            fg_color="#FFFFFF", text_color=COLORES["texto"],
            placeholder_text="Escribe tu pregunta...",
            font=ctk.CTkFont(size=15), placeholder_text_color="#56606C")
        self.entrada.grid(row=1, column=0, sticky="ew", padx=(12, 8), pady=(0, 11))
        self.entrada.bind("<Return>", self.enviar)
        self.boton = ctk.CTkButton(
            inferior, text="Enviar  ➤", width=105, height=47, corner_radius=9,
            fg_color=COLORES["principal"], hover_color=COLORES["principal_hover"],
            font=ctk.CTkFont(size=15, weight="bold"), command=self.enviar)
        self.boton.grid(row=1, column=1, padx=(0, 12), pady=(0, 11))

        self._mostrar_mensaje("asistente", "Hola, ¿qué te gustaría estudiar? Puedes consultar carreras, instituciones o áreas de interés.")

    def _agregar_texto(self, padre, texto, tamano=15, negrita=False, margen=(0, 7)):
        """Etiqueta nativa que ajusta párrafos a la anchura interior real.

        Las etiquetas CustomTkinter pueden recortar las últimas letras cuando
        cambian las dimensiones de tarjetas con varias columnas.
        """
        etiqueta = tk.Label(
            padre, text=texto, bg=padre.cget("bg"), fg=COLORES["texto"],
            font=("Segoe UI", tamano, "bold" if negrita else "normal"),
            justify="left", anchor="w", bd=0, highlightthickness=0,
            wraplength=320)
        etiqueta.pack(anchor="w", fill="x", padx=14, pady=margen)
        self._etiquetas_adaptables.append((etiqueta, padre))
        padre.bind("<Configure>", self._ajustar_textos, add="+")
        return etiqueta

    def _ajustar_textos(self, _evento=None):
        """Recalcula los saltos de línea sin establecer ancho fijo al texto."""
        for etiqueta, padre in list(self._etiquetas_adaptables):
            try:
                if not etiqueta.winfo_exists():
                    self._etiquetas_adaptables.remove((etiqueta, padre))
                    continue
                ancho = padre.winfo_width()
                if ancho > 65:
                    disponible = max(80, ancho - 32)
                    if etiqueta.cget("wraplength") != disponible:
                        etiqueta.configure(wraplength=disponible)
            except (tk.TclError, ValueError):
                pass

    def _mostrar_mensaje(self, rol, mensaje, paginacion=None, afinidades=None):
        if not mensaje.strip():
            return
        fila = self.mensajes
        self.mensajes += 1
        es_usuario = rol == "estudiante"
        contenedor = ctk.CTkFrame(self.historial, fg_color="transparent")
        contenedor.grid(row=fila, column=0, sticky="ew", padx=16, pady=(12, 2))
        contenedor.grid_columnconfigure(0, weight=1)

        fondo_burbuja = (COLORES["mensaje_usuario"] if es_usuario
                          else COLORES["blanco"])
        burbuja = tk.Frame(
            contenedor, bg=fondo_burbuja,
            highlightbackground=COLORES["borde"], highlightcolor=COLORES["borde"],
            highlightthickness=1, bd=0)
        burbuja.grid(row=0, column=0, sticky="ew",
                     padx=(55, 0) if es_usuario else (0, 25))
        tk.Label(burbuja, text="ESTUDIANTE" if es_usuario else "ASISTENTE",
                 fg=COLORES["texto"], bg=fondo_burbuja,
                 font=("Segoe UI", 12, "bold"),
                 anchor="w", bd=0).pack(anchor="w", fill="x", padx=14,
                                        pady=(12, 5))
        if es_usuario:
            self._agregar_texto(burbuja, mensaje, tamano=15, margen=(0, 13))
        else:
            self._presentar_respuesta(burbuja, mensaje)
            if afinidades:
                self._controles_afinidades(burbuja, afinidades)
            if paginacion:
                self._controles_paginacion(burbuja, paginacion)
        self.after(80, self._ajustar_textos)
        self.after(140, self._ir_al_final)

    def _controles_paginacion(self, contenedor, datos):
        """Presenta la navegación dentro de la respuesta correspondiente."""
        barra = tk.Frame(contenedor, bg=COLORES['blanco'])
        barra.pack(fill='x', padx=12, pady=(4, 12))
        pagina, paginas = datos['pagina'], datos['paginas']
        tk.Label(barra, text=f'Página {pagina} de {paginas}',
                 bg=COLORES['blanco'], fg=COLORES['texto'],
                 font=('Segoe UI', 11, 'bold')).pack(side='left', padx=5)
        siguiente = ctk.CTkButton(
            barra, text='Siguiente  →', width=125,
            fg_color=COLORES['principal'], hover_color=COLORES['principal_hover'],
            command=lambda: self._pedir_pagina(datos, pagina + 1))
        siguiente.pack(side='right', padx=4)
        anterior = ctk.CTkButton(
            barra, text='←  Anterior', width=125,
            fg_color=COLORES['principal'], hover_color=COLORES['principal_hover'],
            command=lambda: self._pedir_pagina(datos, pagina - 1))
        anterior.pack(side='right', padx=4)
        if pagina <= 1:
            anterior.configure(state='disabled')
        if pagina >= paginas:
            siguiente.configure(state='disabled')

    def _pedir_pagina(self, datos, pagina):
        if self.en_proceso or self.motor is None or not (1 <= pagina <= datos['paginas']):
            return
        self.en_proceso = True
        self._habilitar(False)
        self.estado.configure(text='Cargando página de resultados...',
                              text_color=COLORES['muted'])
        self.solicitudes.put(('pagina', {'pagina': pagina,
                                      'busqueda': datos['busqueda']}))

    def _desactivar_afinidades(self):
        """Desactiva botones de propuestas anteriores."""
        self._confirmacion_afinidades = None

        for boton in self._botones_afinidades:
            try:
                if boton.winfo_exists():
                    boton.configure(state='disabled')
            except tk.TclError:
                pass

        self._botones_afinidades.clear()

    def _controles_afinidades(self, contenedor, datos):
        """Muestra los botones de alternativas."""
        if not isinstance(datos, dict) or not datos.get('cantidad'):
            return

        self._desactivar_afinidades()
        self._confirmacion_afinidades = dict(datos)

        barra = tk.Frame(contenedor, bg=COLORES['blanco'])
        barra.pack(fill='x', padx=14, pady=(5, 14))

        aceptar = ctk.CTkButton(
            barra,
            text='Ver opciones afines',
            width=190,
            height=36,
            fg_color=COLORES['principal'],
            hover_color=COLORES['principal_hover'],
            command=lambda: self._elegir_afinidades(datos, True)
        )
        aceptar.pack(side='left', padx=(0, 8))

        rechazar = ctk.CTkButton(
            barra,
            text='No, gracias',
            width=130,
            height=36,
            fg_color=COLORES['barra'],
            hover_color='#C5CED9',
            text_color=COLORES['texto'],
            command=lambda: self._elegir_afinidades(datos, False)
        )
        rechazar.pack(side='left')

        self._botones_afinidades.extend((aceptar, rechazar))

    def _elegir_afinidades(self, datos, aceptar):
        if (
            self.en_proceso
            or self.motor is None
            or self._confirmacion_afinidades is None
            or datos.get('busqueda') != self._confirmacion_afinidades.get('busqueda')
        ):
            return

        self._desactivar_afinidades()

        self._mostrar_mensaje(
            'estudiante',
            'Si, mostrar opciones afines.' if aceptar else 'No, gracias.'
        )

        self.en_proceso = True
        self._habilitar(False)

        self.estado.configure(
            text='Consultando opciones afines...' if aceptar
                 else 'Actualizando conversacion...',
            text_color=COLORES['muted']
        )

        self.solicitudes.put((
            'afinidades',
            {'busqueda': datos['busqueda'], 'aceptar': aceptar}
        ))

    def _presentar_respuesta(self, contenedor, mensaje):
        """Conserva los datos recuperados y organiza las ofertas en fichas."""
        ofertas, otras = [], []
        for linea in mensaje.splitlines():
            limpia = linea.strip()
            if limpia.startswith("- ") and " | " in limpia:
                ofertas.append(limpia[2:].split(" | "))
            elif limpia:
                otras.append(limpia)

        for i, linea in enumerate(otras):
            self._agregar_texto(contenedor, linea, tamano=15,
                               negrita=(i == 0), margen=(0, 7))

        if ofertas:
            rejilla = tk.Frame(contenedor, bg=COLORES["blanco"], bd=0)
            rejilla.pack(fill="x", padx=10, pady=(5, 12))
            for columna in (0, 1):
                rejilla.grid_columnconfigure(columna, weight=1, uniform="ofertas")
            for n, campos in enumerate(ofertas):
                if len(campos) >= 4:
                    institucion, programa, plantel, modalidad = campos[:4]
                elif len(campos) == 3:
                    programa, institucion, modalidad = campos
                    plantel = "Plantel no especificado"
                else:
                    programa, institucion, plantel, modalidad = (
                        " · ".join(campos), "", "", "")
                tarjeta = tk.Frame(
                    rejilla, bg=COLORES["tarjeta"],
                    highlightbackground=COLORES["borde"],
                    highlightcolor=COLORES["borde"],
                    highlightthickness=1, bd=0)
                tarjeta.grid(row=n // 2, column=n % 2, sticky="nsew",
                             padx=5, pady=5)
                self._agregar_texto(tarjeta, programa, tamano=13,
                                   negrita=True, margen=(10, 5))
                for detalle in (institucion, plantel, modalidad):
                    if detalle:
                        self._agregar_texto(tarjeta, detalle, tamano=12,
                                           margen=(0, 5))
                tk.Frame(tarjeta, height=5, bg=COLORES["tarjeta"]).pack()
        else:
            tk.Frame(contenedor, height=5, bg=COLORES["blanco"]).pack()

    def _actualizar_region_historial(self, _evento=None):
        """La barra representa únicamente los píxeles ocupados por mensajes."""
        caja = self.lienzo_historial.bbox("all")
        if caja:
            self.lienzo_historial.configure(scrollregion=(0, 0, caja[2], caja[3]))

    def _ajustar_ancho_historial(self, evento):
        """El contenido usa el ancho visible, sin expansión horizontal extra."""
        self.lienzo_historial.itemconfigure(self._historial_ventana, width=evento.width)
        self._actualizar_region_historial()
        self._ajustar_textos()

    def _cursor_sobre_historial(self, evento):
        widget = self.winfo_containing(evento.x_root, evento.y_root)
        while widget is not None:
            if widget is self.historial or widget is self.lienzo_historial:
                return True
            widget = getattr(widget, "master", None)
        return False

    def _desplazar_historial(self, evento):
        """Desplazamiento único y acotado para rueda y touchpad de Windows."""
        if not self._cursor_sobre_historial(evento):
            return None
        if self.lienzo_historial.yview() == (0.0, 1.0):
            return "break"  # Sin contenido que desplazar.

        if getattr(evento, "num", None) in (4, 5):
            pasos = -3 if evento.num == 4 else 3
        else:
            delta = getattr(evento, "delta", 0)
            if not delta:
                return "break"
            self._rueda_acumulada += delta
            pasos = -int(self._rueda_acumulada / 40)
            self._rueda_acumulada += pasos * 40
            if not pasos:
                return "break"
            pasos = max(-12, min(12, pasos))

        self.lienzo_historial.yview_scroll(pasos, "units")
        return "break"

    def _ir_al_final(self):
        self._actualizar_region_historial()
        self.lienzo_historial.yview_moveto(1.0)

    def _habilitar(self, habilitado):
        estado = "normal" if habilitado else "disabled"
        self.entrada.configure(state=estado)
        self.boton.configure(state=estado)
        if habilitado:
            self.entrada.focus_set()

    def _obtener_contrasena(self):
        if keyring is None:
            messagebox.showerror("Dependencia necesaria", "Instalar keyring en el entorno del proyecto.")
            return None
        try:
            contrasena = keyring.get_password(SERVICIO_CREDENCIALES, CUENTA_CREDENCIALES)
        except Exception as exc:
            messagebox.showerror("Credenciales", f"No se pudo leer el almacén de Windows: {exc}")
            return None
        if contrasena:
            return contrasena
        dialogo = ctk.CTkInputDialog(text="Contraseña local de PostgreSQL:", title="Conexión a PostgreSQL")
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
        self.estado.configure(text="Cargando catálogo y modelos de IA...")
        threading.Thread(target=self._trabajar, args=(contrasena,), daemon=True).start()

    def _trabajar(self, contrasena):
        """Procesa todas las consultas en el mismo hilo y conexión PostgreSQL."""
        try:
            self.motor = MotorEducativo(contrasena=contrasena)
            self.eventos.put(("listo", None))
            while True:
                tipo, dato = self.solicitudes.get()
                if tipo == "cerrar":
                    break
                try:
                    if tipo == "nuevo":
                        from motor_ia.contexto import crear_contexto
                        self.motor.contexto = crear_contexto()
                        self.motor.opciones_pendientes = None
                        self.motor._pag_busqueda += 1
                        self.motor._pag_ofertas = None
                        self.motor._pag_contexto = None
                        self.eventos.put(("nuevo", None))
                    elif tipo == "pregunta":
                        respuesta = self.motor.procesar(dato)
                        self.eventos.put(("respuesta", respuesta))
                    elif tipo == "afinidades":
                        self.eventos.put(("respuesta", self.motor.resolver_afinidades(dato)))
                    elif tipo == "pagina":
                        self.eventos.put(("respuesta", self.motor.obtener_pagina(dato)))
                        # La despedida termina la conversación, no el motor.
                        # "Nueva conversación" reutiliza los modelos ya cargados.
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
                    self.estado.configure(text="● Motor preparado · Consultas disponibles",
                                           text_color=COLORES["exito"])
                    self._habilitar(True)
                elif tipo == "respuesta":
                    self._desactivar_afinidades()
                    if valor.get("mensaje"):
                        self._mostrar_mensaje("asistente", valor["mensaje"],
                                              paginacion=valor.get("paginacion"),
                                              afinidades=valor.get("afinidades"))
                    self.en_proceso = False
                    if valor.get("cerrar"):
                        self.estado.configure(text="Sesión finalizada")
                        self._habilitar(False)
                    else:
                        self.estado.configure(text="● Motor preparado · Consultas disponibles",
                                               text_color=COLORES["exito"])
                        self._habilitar(True)
                elif tipo == "nuevo":
                    for widget in self.historial.winfo_children():
                        widget.destroy()
                    self.mensajes = 0
                    self._etiquetas_adaptables.clear()
                    self._rueda_acumulada = 0
                    self.lienzo_historial.yview_moveto(0)
                    self.after_idle(self._actualizar_region_historial)
                    self._mostrar_mensaje("asistente", "Nueva conversación iniciada. ¿Qué te gustaría estudiar?")
                    self.en_proceso = False
                    self.estado.configure(text="● Nueva conversación preparada",
                                           text_color=COLORES["exito"])
                    self._habilitar(True)
                elif tipo == "error_consulta":
                    self._mostrar_mensaje("asistente", "No se pudo procesar la consulta: " + valor)
                    self.en_proceso = False
                    self.estado.configure(text="Motor preparado", text_color=COLORES["exito"])
                    self._habilitar(True)
                elif tipo == "error_inicio":
                    self._mostrar_mensaje("asistente", "No se pudo iniciar el motor: " + valor)
                    self.estado.configure(text="Error de inicialización", text_color="#B63B3B")
                elif tipo == "finalizado":
                    self._habilitar(False)
                    if not self.estado.cget("text").startswith("Error"):
                        self.estado.configure(text="Sesión finalizada")
        except queue.Empty:
            pass
        self.after(100, self._procesar_eventos)

    def _ejemplo(self, texto):
        if self.en_proceso or self.motor is None:
            return
        self.entrada.delete(0, "end")
        self.entrada.insert(0, texto)
        self.entrada.focus_set()

    def enviar(self, _evento=None):
        if self.en_proceso or self.motor is None:
            return
        pregunta = self.entrada.get().strip()
        if not pregunta:
            return
        self._desactivar_afinidades()
        self.entrada.delete(0, "end")
        self._mostrar_mensaje("estudiante", pregunta)
        self.en_proceso = True
        self._habilitar(False)
        self.estado.configure(text="Consultando catálogo y procesando respuesta...",
                               text_color=COLORES["muted"])
        self.solicitudes.put(("pregunta", pregunta))

    def nueva_conversacion(self):
        if self.en_proceso or self.motor is None:
            return
        self._desactivar_afinidades()
        self.en_proceso = True
        self._habilitar(False)
        self.solicitudes.put(("nuevo", None))

    def cerrar(self):
        self.cerrando = True
        self.solicitudes.put(("cerrar", None))
        self.destroy()


if __name__ == "__main__":
    InterfazEducativa().mainloop()
