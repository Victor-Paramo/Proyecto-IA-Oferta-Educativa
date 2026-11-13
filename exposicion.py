import tkinter as tk
from tkinter import ttk, messagebox


NAVY = "#142C43"
NAVY_DARK = "#10263A"
LIGHT_BG = "#F3F5F7"
CARD_BG = "#FFFFFF"
SOFT_GRAY = "#E6EBF0"
MID_GRAY = "#D3DCE5"
TEXT = "#111111"
MUTED = "#4F6478"
CODE_BG = "#F8FAFC"


PREGUNTAS_DEMOSTRACION = [
    (
        "Catalogo general - 6 carreras por pagina",
        [
            "¿Qué carreras puedo estudiar en CDMX?",
            "Muéstrame todas las licenciaturas."
        ]
    ),
    (
        "Cobertura tematica y opciones afines",
        [
            "Quiero pronosticar huracanes.",
            "Me gustaría estudiar Astronomía y observar las estrellas.",
            "Quiero desarrollar aplicaciones de realidad aumentada.",
            "Me interesa diseñar cohetes y naves espaciales.",
            "Quiero investigar si existe vida extraterrestre."
        ]
    ),
    (
        "Consulta directa y memoria conversacional",
        [
            "¿Qué carreras ofrece la Universidad ICEL?",
            "¿Y cuáles son mixtas?",
            "¿Y cuáles son escolarizadas?"
        ]
    ),
    (
        "Busqueda semantica con MiniLM",
        [
            "Me gustaría desarrollar videojuegos y programar mundos virtuales.",
            "¿Y cuáles de esas opciones son mixtas?",
            "¿Y cuáles son escolarizadas?"
        ]
    ),
    (
        "Busquedas amplias y limites del sistema",
        [
            "Muéstrame todas las ingenierías.",
            "¿Qué carreras puedo estudiar en línea?",
            "¿Qué carreras ofrece la UNAM?",
            "¿Cuánto cuesta estudiar Derecho?",
            "Muchas gracias, nos vemos pronto."
        ]
    )
]


INDICE_TECNICO = [
    {
        "menu": "01  Entrada de preguntas",
        "pregunta": "1. ¿Cómo se maneja la cadena de entrada (la pregunta del usuario)?",
        "archivos": [
            (
                "interfaz_escritorio.py",
                [
                    ("enviar()", "Obtiene la pregunta del estudiante y la manda al motor."),
                    ("_procesar_eventos()", "Recibe la respuesta y actualiza la interfaz.")
                ]
            ),
            (
                "motor_ia/entidades.py",
                [
                    ("normalizar_texto()", "Uniforma el texto para facilitar el análisis.")
                ]
            ),
            (
                "app.py",
                [
                    ("MotorEducativo.procesar()", "Coordina todo el flujo de procesamiento.")
                ]
            )
        ],
        "codigos": [
            (
                "interfaz_escritorio.py - enviar()",
                """pregunta = self.entrada.get().strip()

if not pregunta:
    return

self._mostrar_mensaje("estudiante", pregunta)
self.solicitudes.put(("pregunta", pregunta))"""
            ),
            (
                "interfaz_escritorio.py - trabajo en segundo plano",
                """elif tipo == "pregunta":
    respuesta = self.motor.procesar(dato)
    self.eventos.put(("respuesta", respuesta))"""
            ),
            (
                "motor_ia/entidades.py - normalizar_texto()",
                """texto = texto.lower()
texto = unicodedata.normalize("NFD", texto)

texto = "".join(
    c for c in texto
    if unicodedata.category(c) != "Mn"
)

texto = re.sub(r"[^a-z0-9\\s]", " ", texto)
texto = re.sub(r"\\s+", " ", texto).strip()

return texto"""
            )
        ]
    },
    {
        "menu": "02  TF-IDF",
        "pregunta": "2. ¿Qué es TF-IDF y cómo transforma una cadena de texto en valores numéricos?",
        "archivos": [
            (
                "motor_ia/interpretar_consulta.py",
                [
                    ("preparar_clasificador()", "Construye el pipeline con TF-IDF."),
                    ("TfidfVectorizer(...)", "Vectoriza palabras y caracteres."),
                    ("FeatureUnion()", "Combina ambas representaciones.")
                ]
            )
        ],
        "codigos": [
            (
                "Pipeline TF-IDF",
                """modelo = Pipeline([
    ("tfidf", FeatureUnion([
        ("palabras", TfidfVectorizer(
            ngram_range=(1, 2)
        )),
        ("caracteres", TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5)
        ))
    ])),
    ("clasificador", LogisticRegression(
        max_iter=2000
    ))
])"""
            ),
            (
                "Entrenamiento del vectorizador",
                """preguntas, intenciones = cargar_entrenamiento()

modelo.fit(preguntas, intenciones)"""
            )
        ]
    },
    {
        "menu": "03  Regresión logística",
        "pregunta": "3. ¿Qué es la regresión logística y cómo clasifica la intención del usuario?",
        "archivos": [
            (
                "motor_ia/interpretar_consulta.py",
                [
                    ("preparar_clasificador()", "Crea y entrena el clasificador."),
                    ("interpretar_pregunta()", "Predice la intención de la consulta."),
                    ("modelo.predict()", "Selecciona la intención final."),
                    ("modelo.predict_proba()", "Obtiene probabilidades de las 4 intenciones.")
                ]
            )
        ],
        "codigos": [
            (
                "Configuración del clasificador",
                """("clasificador", LogisticRegression(
    max_iter=2000
))"""
            ),
            (
                "Predicción de intención",
                """texto = normalizar_texto(pregunta)

intencion = modelo.predict([texto])[0]
probabilidades = modelo.predict_proba([texto])[0]
confianza = float(max(probabilidades))"""
            )
        ]
    },
    {
        "menu": "04  Reconocimiento de entidades",
        "pregunta": "4. ¿Cómo funciona el reconocimiento de entidades en nuestro Proyecto IA?",
        "archivos": [
            (
                "motor_ia/entidades.py",
                [
                    ("cargar_instituciones()", "Carga instituciones desde PostgreSQL."),
                    ("cargar_programas()", "Carga programas académicos."),
                    ("extraer_institucion()", "Busca instituciones mencionadas."),
                    ("extraer_programa()", "Busca carreras o programas."),
                    ("extraer_modalidad()", "Reconoce modalidades educativas."),
                    ("normalizar_texto()", "Ayuda a comparar cadenas.")
                ]
            ),
            (
                "motor_ia/interpretar_modalidades.py",
                [
                    ("analizar_modalidades()", "Analiza modalidades y negaciones."),
                    ("ajustar_interpretacion()", "Integra modalidad a la interpretación.")
                ]
            )
        ],
        "codigos": [
            (
                "Carga de instituciones",
                """with conexion.cursor() as cursor:
    cursor.execute(\"\"\"
        SELECT id_institucion, nombre
        FROM catalogo.institucion
        ORDER BY LENGTH(nombre) DESC
    \"\"\")
    return cursor.fetchall()"""
            ),
            (
                "Extracción de institución",
                """texto = normalizar_texto(pregunta)

for id_institucion, nombre in instituciones:
    nombre_normalizado = normalizar_texto(nombre)

    if f" {nombre_normalizado} " in f" {texto} ":
        return {
            "id_institucion": id_institucion,
            "nombre": nombre
        }"""
            ),
            (
                "Interpretación de modalidades",
                """for inicio, _, modalidad in spans:
    previo = texto[max(0, inicio - 115):inicio]

    destino = excluidas if NEGACION_PREVIA.search(previo) else solicitadas

    if modalidad not in destino:
        destino.append(modalidad)"""
            )
        ]
    },
    {
        "menu": "05  Memoria y contexto",
        "pregunta": "5. ¿Cómo funciona la memoria conversacional y la gestión del contexto?",
        "archivos": [
            (
                "motor_ia/contexto.py",
                [
                    ("crear_contexto()", "Inicializa la memoria."),
                    ("actualizar_contexto()", "Conserva o modifica filtros."),
                    ("es_seguimiento()", "Detecta continuidad de preguntas."),
                    ("es_seguimiento_estructurado()", "Detecta seguimiento sobre filtros."),
                    ("mostrar_contexto()", "Presenta el estado del contexto.")
                ]
            ),
            (
                "app.py",
                [
                    ("Bloque de conservación", "Conserva programas semánticos y filtros."),
                    ("Bloque de reinicio", "Reinicia el contexto en nueva conversación.")
                ]
            )
        ],
        "codigos": [
            (
                "Crear contexto",
                """def crear_contexto():
    return {
        "institucion": None,
        "programa": None,
        "modalidad": None,
        "programas_semanticos": []
    }"""
            ),
            (
                "Actualizar contexto",
                """if conservar:
    nuevo = contexto.copy()
else:
    nuevo = crear_contexto()

if interpretacion["institucion"] is not None:
    nuevo["institucion"] = interpretacion["institucion"]

if interpretacion["programa"] is not None:
    nuevo["programa"] = interpretacion["programa"]

if modalidad is not None:
    nuevo["modalidad"] = modalidad"""
            ),
            (
                "Conservación de programas semánticos",
                """nuevo_contexto["programas_semanticos"] = list(
    contexto["programas_semanticos"]
)"""
            )
        ]
    },
    {
        "menu": "06  Decisión SQL o MiniLM",
        "pregunta": "6. ¿Cómo decide nuestro Proyecto IA si debe consultar PostgreSQL o utilizar MiniLM?",
        "archivos": [
            (
                "motor_ia/interpretar_consulta.py",
                [
                    ("interpretar_pregunta()", "Devuelve intención y entidades detectadas.")
                ]
            ),
            (
                "motor_ia/validacion_cobertura_tematica.py",
                [
                    ("es_exploracion_tematica()", "Detecta si la consulta expresa intereses temáticos.")
                ]
            ),
            (
                "app.py",
                [
                    ("MotorEducativo.procesar()", "Decide la ruta de búsqueda."),
                    ("buscar_categoria_general()", "Atiende búsquedas amplias."),
                    ("Bloque de decisión", "Selecciona SQL o MiniLM según la consulta.")
                ]
            )
        ],
        "codigos": [
            (
                "Interpretación inicial",
                """interpretacion = interpretar_pregunta(
    pregunta,
    modelo,
    instituciones,
    programas
)"""
            ),
            (
                "Evaluación de exploración temática",
                """explorar_tema = (
    False if seguimiento_estructurado
    else exploracion_explicita
         or consulta_combinada
         or es_exploracion_tematica(interpretacion)
)"""
            ),
            (
                "Pseudocódigo de decisión",
                """SI la consulta es temática:
    validar cobertura temática

    SI hay cobertura directa:
        usar MiniLM
    SI no hay cobertura:
        aclarar o proponer afinidades

SI la consulta no es temática:
    usar búsqueda SQL directa"""
            )
        ]
    },
    {
        "menu": "07  MiniLM y embeddings",
        "pregunta": "7. ¿Qué es MiniLM, cómo genera embeddings y cómo calcula la similitud semántica?",
        "archivos": [
            (
                "motor_ia/busqueda_semantica.py",
                [
                    ("cargar_programas()", "Recupera programas con ofertas."),
                    ("buscar_semanticamente()", "Compara embeddings y ordena resultados.")
                ]
            ),
            (
                "app.py",
                [
                    ("SentenceTransformer()", "Carga MiniLM."),
                    ("modelo_semantico.encode()", "Genera embeddings del catálogo."),
                    ("Filtrado de embeddings", "Limita a programas permitidos por cobertura.")
                ]
            )
        ],
        "codigos": [
            (
                "Carga del modelo semántico",
                """self.modelo_semantico = SentenceTransformer(
    str(RUTA_MODELO)
)"""
            ),
            (
                "Embeddings del catálogo",
                """nombres = [nombre for _, nombre in self.programas_semanticos]

self.vectores_semanticos = self.modelo_semantico.encode(
    nombres,
    convert_to_tensor=True,
    show_progress_bar=False
)"""
            ),
            (
                "Similitud del coseno y top-k",
                """vector_pregunta = modelo.encode(
    pregunta,
    convert_to_tensor=True
)

similitudes = util.cos_sim(
    vector_pregunta, vectores
)[0]

indices = similitudes.topk(
    k=min(limite, len(programas))
).indices.tolist()"""
            )
        ]
    },
    {
        "menu": "08  Recuperación y respuestas",
        "pregunta": "8. ¿Cómo recupera nuestro Proyecto IA las ofertas educativas de PostgreSQL y construye la respuesta final?",
        "archivos": [
            (
                "motor_ia/recuperacion_semantica.py",
                [
                    ("recuperar_ofertas()", "Recupera ofertas de programas elegidos por MiniLM.")
                ]
            ),
            (
                "funciones/buscar_programa.py",
                [
                    ("buscar_programa()", "Consulta ofertas de una carrera.")
                ]
            ),
            (
                "motor_ia/generador_respuestas.py",
                [
                    ("respuesta_ofertas()", "Construye mensajes con ofertas."),
                    ("respuesta_programas()", "Presenta programas relacionados."),
                    ("respuesta_sin_cobertura()", "Explica ausencia de cobertura directa."),
                    ("respuesta_afinidades()", "Presenta alternativas afines.")
                ]
            ),
            (
                "interfaz_escritorio.py",
                [
                    ("_mostrar_mensaje()", "Muestra mensajes y tarjetas."),
                    ("Paginación", "Divide resultados en grupos.")
                ]
            )
        ],
        "codigos": [
            (
                "Recuperación de ofertas",
                """for candidato in candidatos:
    ofertas = buscar_programa(
        conexion,
        id_programa=candidato["id_programa"]
    )

    resultados.append({
        "programa": candidato["nombre"],
        "similitud": candidato["similitud"],
        "ofertas": ofertas
    })"""
            ),
            (
                "Construcción de respuesta",
                """for resultado in resultados:
    ofertas = resultado["ofertas"]

    if ofertas:
        lineas.extend(
            _resumen_instituciones(
                resultado["programa"],
                ofertas
            )
        )"""
            ),
            (
                "Salida a la interfaz",
                """self._mostrar_mensaje(
    "asistente",
    valor["mensaje"],
    paginacion=valor.get("paginacion")
)"""
            )
        ]
    },
    {
        "menu": "09  Cobertura temática",
        "pregunta": "9. ¿Cómo funcionan las validaciones de cobertura temática y por qué evitamos recomendar carreras sin suficiente evidencia?",
        "archivos": [
            (
                "motor_ia/validacion_cobertura_tematica.py",
                [
                    ("detectar_temas()", "Reconoce áreas académicas mediante reglas."),
                    ("priorizar_temas()", "Da prioridad a especialidades."),
                    ("construir_indice()", "Relaciona programas reales con áreas."),
                    ("comprobar_cobertura()", "Verifica evidencia directa."),
                    ("es_exploracion_tematica()", "Identifica consultas temáticas.")
                ]
            ),
            (
                "motor_ia/afinidades_academicas.py",
                [
                    ("buscar_afinidades()", "Busca alternativas relacionadas.")
                ]
            ),
            (
                "app.py",
                [
                    ("Bloque de cobertura", "Evalúa cobertura_directa, aclaración y restricciones.")
                ]
            )
        ],
        "codigos": [
            (
                "Detección de temas",
                """texto = normalizar(pregunta)

return sorted(
    area
    for area, patrones in PATRONES.items()
    if any(p.search(texto) for p in patrones)
)"""
            ),
            (
                "Comprobación de cobertura",
                """temas = detectar_temas(pregunta)
temas_prioritarios = priorizar_temas(temas)

ids = {
    id_programa
    for area in temas_prioritarios
    if indice.get(area)
    for id_programa, _ in indice.get(area, ())
}"""
            ),
            (
                "Restricción de programas permitidos",
                """programas_permitidos = [
    programas_semanticos[i]
    for i in indices_permitidos
]"""
            )
        ]
    },
    {
        "menu": "10  Entrenamiento y evaluación",
        "pregunta": "10. ¿Cómo se entrenó, evaluó y mejoró nuestro clasificador de intenciones utilizando las 136 preguntas de entrenamiento?",
        "archivos": [
            (
                "datos/intenciones_entrenamiento.csv",
                [
                    ("Bloque de datos", "Contiene 136 preguntas con 4 intenciones.")
                ]
            ),
            (
                "motor_ia/interpretar_consulta.py",
                [
                    ("cargar_entrenamiento()", "Lee preguntas y etiquetas."),
                    ("preparar_clasificador()", "Entrena TF-IDF y regresión logística."),
                    ("modelo.fit()", "Ajusta el clasificador.")
                ]
            ),
            (
                "motor_ia/clasificador.py",
                [
                    ("cargar_datos()", "Carga los datos para evaluación."),
                    ("entrenar_modelo()", "Divide datos, entrena y calcula métricas."),
                    ("probar_modelo()", "Permite probar preguntas nuevas."),
                    ("train_test_split()", "Separa entrenamiento y prueba."),
                    ("accuracy_score()", "Calcula exactitud."),
                    ("classification_report()", "Calcula precisión, recall y F1-score.")
                ]
            ),
            (
                "comparar_intenciones_actualizado.py",
                [
                    ("construir_modelo()", "Construye configuraciones de modelo."),
                    ("ejecutar_comparacion()", "Compara versiones del clasificador.")
                ]
            )
        ],
        "codigos": [
            (
                "Lectura del CSV",
                """with open(
    ARCHIVO_CSV,
    "r",
    encoding="utf-8-sig",
    newline=""
) as archivo:
    lector = csv.DictReader(archivo)

    for fila in lector:
        preguntas.append(normalizar_texto(fila["pregunta"]))
        intenciones.append(fila["intencion"].strip())"""
            ),
            (
                "Entrenamiento",
                """preguntas, intenciones = cargar_entrenamiento()
modelo.fit(preguntas, intenciones)"""
            ),
            (
                "Evaluación del modelo",
                """X_entrenamiento, X_prueba, y_entrenamiento, y_prueba = train_test_split(
    preguntas,
    intenciones,
    test_size=0.25,
    random_state=42,
    stratify=intenciones
)

modelo.fit(X_entrenamiento, y_entrenamiento)
predicciones = modelo.predict(X_prueba)

exactitud = accuracy_score(y_prueba, predicciones)
reporte = classification_report(y_prueba, predicciones, zero_division=0)"""
            )
        ]
    },
    {
        "menu": "11  SQL en PostgreSQL",
        "pregunta": "11. ¿Cómo realiza nuestro Proyecto IA las consultas SQL en PostgreSQL mediante SELECT, JOIN y WHERE?",
        "archivos": [
            (
                "motor_ia/entidades.py",
                [
                    ("conectar_bd()", "Abre la conexión con PostgreSQL."),
                    ("cargar_instituciones()", "Consulta instituciones."),
                    ("cargar_programas()", "Consulta programas.")
                ]
            ),
            (
                "funciones/buscar_programa.py",
                [
                    ("buscar_programa()", "Consulta ofertas de un programa.")
                ]
            ),
            (
                "funciones/buscar_institucion.py",
                [
                    ("buscar_institucion()", "Recupera ofertas por institución.")
                ]
            ),
            (
                "funciones/filtrar_modalidad.py",
                [
                    ("filtrar_modalidad()", "Filtra por modalidad.")
                ]
            ),
            (
                "motor_ia/recuperacion_semantica.py",
                [
                    ("recuperar_ofertas()", "Consulta ofertas para programas semánticos.")
                ]
            ),
            (
                "app.py",
                [
                    ("buscar_categoria_general()", "Ejecuta SQL con filtros y ordenamientos."),
                    ("cursor.execute()", "Envía SQL a PostgreSQL."),
                    ("cursor.fetchall()", "Recupera resultados.")
                ]
            )
        ],
        "codigos": [
            (
                "Consulta SQL representativa",
                """SELECT
    o.id_oferta,
    i.nombre AS institucion,
    pa.nombre AS programa,
    m.nombre AS modalidad
FROM catalogo.oferta_educativa o
JOIN catalogo.plantel p
    ON p.id_plantel = o.id_plantel
JOIN catalogo.institucion i
    ON i.id_institucion = p.id_institucion
JOIN catalogo.programa_academico pa
    ON pa.id_programa = o.id_programa
JOIN catalogo.modalidad m
    ON m.id_modalidad = o.id_modalidad
WHERE o.id_programa = %s
  AND (%s IS NULL OR m.nombre = %s)
ORDER BY pa.nombre, i.nombre"""
            ),
            (
                "Ejecución en Python",
                """cursor.execute(
    consulta,
    (id_programa, modalidad, modalidad)
)

registros = cursor.fetchall()"""
            ),
            (
                "Filtro por categorías en app.py",
                """WHERE o.id_programa = ANY(%s)
  AND (%s IS NULL OR m.nombre = %s)
  AND (%s IS NULL OR i.id_institucion = %s)

ORDER BY pa.nombre, i.nombre, p.nombre NULLS LAST"""
            )
        ]
    }
]


CONSULTAS_SQL = [
    (
        "Programas distintos del catálogo",
        """SELECT DISTINCT pa.id_programa, pa.nombre
FROM catalogo.programa_academico pa
JOIN catalogo.oferta_educativa o
    ON o.id_programa = pa.id_programa
ORDER BY pa.nombre;"""
    ),
    (
        "Buscar ofertas de un programa",
        """SELECT
    i.nombre AS institucion,
    p.nombre AS plantel,
    pa.nombre AS programa,
    m.nombre AS modalidad
FROM catalogo.oferta_educativa o
JOIN catalogo.plantel p
    ON p.id_plantel = o.id_plantel
JOIN catalogo.institucion i
    ON i.id_institucion = p.id_institucion
JOIN catalogo.programa_academico pa
    ON pa.id_programa = o.id_programa
JOIN catalogo.modalidad m
    ON m.id_modalidad = o.id_modalidad
WHERE pa.nombre ILIKE '%INGENIERIA%'
ORDER BY pa.nombre, i.nombre;"""
    ),
    (
        "Buscar por institución",
        """SELECT
    i.nombre AS institucion,
    pa.nombre AS programa,
    m.nombre AS modalidad
FROM catalogo.oferta_educativa o
JOIN catalogo.plantel p
    ON p.id_plantel = o.id_plantel
JOIN catalogo.institucion i
    ON i.id_institucion = p.id_institucion
JOIN catalogo.programa_academico pa
    ON pa.id_programa = o.id_programa
JOIN catalogo.modalidad m
    ON m.id_modalidad = o.id_modalidad
WHERE i.nombre ILIKE '%ICEL%'
ORDER BY pa.nombre;"""
    ),
    (
        "Buscar por modalidad",
        """SELECT
    pa.nombre AS programa,
    i.nombre AS institucion,
    m.nombre AS modalidad
FROM catalogo.oferta_educativa o
JOIN catalogo.plantel p
    ON p.id_plantel = o.id_plantel
JOIN catalogo.institucion i
    ON i.id_institucion = p.id_institucion
JOIN catalogo.programa_academico pa
    ON pa.id_programa = o.id_programa
JOIN catalogo.modalidad m
    ON m.id_modalidad = o.id_modalidad
WHERE m.nombre = 'MIXTA'
ORDER BY pa.nombre, i.nombre;"""
    ),
    (
        "Contar ofertas totales",
        """SELECT COUNT(*) AS total_ofertas
FROM catalogo.oferta_educativa;"""
    )
]


CONSOLA_APP = [
    (
        "Abrir la interfaz principal",
        """cd C:\\Users\\Admin\\Desktop\\ProyectoIA
.\\.venv\\Scripts\\python.exe interfaz_escritorio.py"""
    ),
    (
        "Abrir este panel de exposición",
        """cd C:\\Users\\Admin\\Desktop\\ProyectoIA
.\\.venv\\Scripts\\python.exe exposicion.py"""
    ),
    (
        "Ejecutar app.py desde consola",
        """cd C:\\Users\\Admin\\Desktop\\ProyectoIA
.\\.venv\\Scripts\\python.exe app.py"""
    ),
    (
        "Pregunta equivalente en consola - consulta directa",
        """Pregunta:
¿Qué carreras ofrece la Universidad ICEL?

Luego:
¿Y cuáles son mixtas?

Luego:
¿Y cuáles son escolarizadas?"""
    ),
    (
        "Pregunta equivalente en consola - MiniLM",
        """Pregunta:
Me gustaría desarrollar videojuegos y programar mundos virtuales.

Luego:
¿Y cuáles de esas opciones son mixtas?

Luego:
¿Y cuáles son escolarizadas?"""
    ),
    (
        "Pregunta equivalente en consola - cobertura temática",
        """Pregunta:
Quiero pronosticar huracanes.

Si aparecen opciones:
ver opciones afines"""
    )
]


class ScrollableFrame(tk.Frame):
    def __init__(self, master, bg=LIGHT_BG, **kwargs):
        super().__init__(master, bg=bg, **kwargs)

        self.canvas = tk.Canvas(
            self,
            bg=bg,
            highlightthickness=0,
            bd=0
        )
        self.scrollbar = tk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )
        self.inner = tk.Frame(self.canvas, bg=bg)

        self.window_id = self.canvas.create_window(
            (0, 0),
            window=self.inner,
            anchor="nw"
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_inner_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def reset_top(self):
        self.canvas.yview_moveto(0)


class ExposicionApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Exposicion - Oferta Educativa CDMX 2.0")
        self.geometry("1600x950")
        self.minsize(1300, 780)
        self.configure(bg=LIGHT_BG)

        self.indice_actual = 0
        self.panel_indice_visible = True

        self._configurar_estilos()
        self._construir_interfaz()

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "TNotebook",
            background=LIGHT_BG,
            borderwidth=0
        )

        style.configure(
            "TNotebook.Tab",
            padding=(18, 12),
            font=("Segoe UI", 12, "bold")
        )

    def _construir_interfaz(self):
        borde_externo = tk.Frame(
            self,
            bg=NAVY,
            highlightthickness=0
        )
        borde_externo.pack(fill="both", expand=True, padx=10, pady=10)

        contenedor = tk.Frame(borde_externo, bg=LIGHT_BG)
        contenedor.pack(fill="both", expand=True, padx=3, pady=3)

        self.notebook = ttk.Notebook(contenedor)
        self.notebook.pack(fill="both", expand=True)

        self.tab_preguntas = tk.Frame(self.notebook, bg=LIGHT_BG)
        self.tab_indice = tk.Frame(self.notebook, bg=LIGHT_BG)
        self.tab_sql = tk.Frame(self.notebook, bg=LIGHT_BG)
        self.tab_consola = tk.Frame(self.notebook, bg=LIGHT_BG)

        self.notebook.add(self.tab_preguntas, text="1 - Preguntas")
        self.notebook.add(self.tab_indice, text="2 - Índice técnico")
        self.notebook.add(self.tab_sql, text="3 - Consultas SQL")
        self.notebook.add(self.tab_consola, text="4 - Consola app.py")

        self._construir_tab_preguntas()
        self._construir_tab_indice()
        self._construir_tab_sql()
        self._construir_tab_consola()

    def copiar_al_portapapeles(self, texto):
        self.clipboard_clear()
        self.clipboard_append(texto)
        self.update()
        messagebox.showinfo("Copiado", "Texto copiado al portapapeles.")

    def _crear_boton_copiar(self, master, texto):
        return tk.Button(
            master,
            text="Copiar",
            command=lambda t=texto: self.copiar_al_portapapeles(t),
            bg=NAVY,
            fg="white",
            activebackground=NAVY_DARK,
            activeforeground="white",
            font=("Segoe UI", 12, "bold"),
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2"
        )

    def _construir_tab_preguntas(self):
        marco = tk.Frame(
            self.tab_preguntas,
            bg=CARD_BG,
            highlightbackground=NAVY,
            highlightthickness=2
        )
        marco.pack(fill="both", expand=True, padx=14, pady=14)

        titulo = tk.Label(
            marco,
            text="Preguntas de demostración",
            bg=CARD_BG,
            fg=NAVY_DARK,
            font=("Segoe UI", 24, "bold")
        )
        titulo.pack(anchor="w", padx=20, pady=(18, 10))

        scroll = ScrollableFrame(marco, bg=CARD_BG)
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        contador = 1
        for seccion, preguntas in PREGUNTAS_DEMOSTRACION:
            lbl = tk.Label(
                scroll.inner,
                text=seccion,
                bg=CARD_BG,
                fg=NAVY_DARK,
                font=("Segoe UI", 18, "bold")
            )
            lbl.pack(anchor="w", padx=10, pady=(12, 8))

            for pregunta in preguntas:
                tarjeta = tk.Frame(
                    scroll.inner,
                    bg="#EEF3F7",
                    highlightbackground="#C9D4DE",
                    highlightthickness=1
                )
                tarjeta.pack(fill="x", padx=8, pady=6)

                num = tk.Label(
                    tarjeta,
                    text=f"{contador:02d}",
                    bg="#EEF3F7",
                    fg="#6A8094",
                    font=("Segoe UI", 16, "bold"),
                    width=4
                )
                num.pack(side="left", padx=(10, 6), pady=14)

                texto = tk.Label(
                    tarjeta,
                    text=pregunta,
                    bg="#EEF3F7",
                    fg="black",
                    font=("Segoe UI", 16),
                    justify="left",
                    anchor="w"
                )
                texto.pack(side="left", fill="x", expand=True, padx=4, pady=14)

                boton = self._crear_boton_copiar(tarjeta, pregunta)
                boton.pack(side="right", padx=12, pady=10)

                contador += 1

    def _construir_tab_indice(self):
        marco = tk.Frame(
            self.tab_indice,
            bg=CARD_BG,
            highlightbackground=NAVY,
            highlightthickness=2
        )
        marco.pack(fill="both", expand=True, padx=14, pady=14)

        encabezado = tk.Frame(marco, bg=NAVY)
        encabezado.pack(fill="x")

        tk.Label(
            encabezado,
            text="ÍNDICE TÉCNICO",
            bg=NAVY,
            fg="white",
            font=("Segoe UI", 28, "bold")
        ).pack(anchor="w", padx=24, pady=(18, 4))

        tk.Label(
            encabezado,
            text="Proyecto IA: Oferta Educativa CDMX 2.0  ·  11 preguntas de estudio",
            bg=NAVY,
            fg="#DDE8F0",
            font=("Segoe UI", 14)
        ).pack(anchor="w", padx=24, pady=(0, 18))

        barra = tk.Frame(marco, bg=LIGHT_BG)
        barra.pack(fill="x", padx=16, pady=(14, 8))

        self.boton_panel = tk.Button(
            barra,
            text="Ocultar panel de preguntas",
            command=self._alternar_panel_indice,
            bg=NAVY,
            fg="white",
            activebackground=NAVY_DARK,
            activeforeground="white",
            font=("Segoe UI", 12, "bold"),
            bd=0,
            padx=16,
            pady=8,
            cursor="hand2"
        )
        self.boton_panel.pack(side="left")

        tk.Label(
            barra,
            text="Muestra archivos, funciones y fragmentos representativos del código.",
            bg=LIGHT_BG,
            fg=MUTED,
            font=("Segoe UI", 13)
        ).pack(side="left", padx=14)

        cuerpo = tk.Frame(marco, bg=LIGHT_BG)
        cuerpo.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)

        self.panel_izquierdo = tk.Frame(
            cuerpo,
            bg="#EFF3F7",
            highlightbackground="#C7D1DB",
            highlightthickness=1
        )
        self.panel_izquierdo.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        self.panel_izquierdo.grid_rowconfigure(1, weight=1)

        tk.Label(
            self.panel_izquierdo,
            text="CONTENIDO",
            bg="#EFF3F7",
            fg=NAVY_DARK,
            font=("Segoe UI", 17, "bold")
        ).pack(anchor="w", padx=16, pady=(16, 10))

        self.scroll_menu = ScrollableFrame(self.panel_izquierdo, bg="#EFF3F7")
        self.scroll_menu.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.botones_indice = []
        for i, item in enumerate(INDICE_TECNICO):
            btn = tk.Button(
                self.scroll_menu.inner,
                text=item["menu"],
                anchor="w",
                justify="left",
                bg="white",
                fg=NAVY_DARK,
                activebackground="#D3DFE8",
                activeforeground=NAVY_DARK,
                font=("Segoe UI", 15, "bold"),
                bd=0,
                padx=16,
                pady=16,
                cursor="hand2",
                command=lambda idx=i: self._mostrar_indice_tecnico(idx)
            )
            btn.pack(fill="x", pady=4)
            self.botones_indice.append(btn)

        self.panel_derecho = tk.Frame(
            cuerpo,
            bg=CARD_BG,
            highlightbackground="#C7D1DB",
            highlightthickness=1
        )
        self.panel_derecho.grid(row=0, column=1, sticky="nsew")
        self.panel_derecho.grid_rowconfigure(1, weight=1)
        self.panel_derecho.grid_columnconfigure(0, weight=1)

        self.encabezado_derecho = tk.Frame(self.panel_derecho, bg="#DDE7EF")
        self.encabezado_derecho.grid(row=0, column=0, sticky="ew")

        self.lbl_panel_titulo = tk.Label(
            self.encabezado_derecho,
            text="ARCHIVOS, FUNCIONES Y FRAGMENTOS REPRESENTATIVOS",
            bg="#DDE7EF",
            fg=NAVY_DARK,
            font=("Segoe UI", 18, "bold")
        )
        self.lbl_panel_titulo.pack(anchor="w", padx=18, pady=14)

        self.scroll_contenido_indice = ScrollableFrame(self.panel_derecho, bg=CARD_BG)
        self.scroll_contenido_indice.grid(row=1, column=0, sticky="nsew")

        self._mostrar_indice_tecnico(0)

    def _alternar_panel_indice(self):
        if self.panel_indice_visible:
            self.panel_izquierdo.grid_remove()
            self.boton_panel.configure(text="Mostrar panel de preguntas")
            self.panel_indice_visible = False
        else:
            self.panel_izquierdo.grid()
            self.boton_panel.configure(text="Ocultar panel de preguntas")
            self.panel_indice_visible = True

    def _limpiar_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

    def _mostrar_indice_tecnico(self, indice):
        self.indice_actual = indice
        item = INDICE_TECNICO[indice]

        for i, btn in enumerate(self.botones_indice):
            if i == indice:
                btn.configure(
                    bg=NAVY,
                    fg="white",
                    activebackground=NAVY,
                    activeforeground="white"
                )
            else:
                btn.configure(
                    bg="white",
                    fg=NAVY_DARK,
                    activebackground="#D3DFE8",
                    activeforeground=NAVY_DARK
                )

        contenedor = self.scroll_contenido_indice.inner
        self._limpiar_frame(contenedor)

        titulo = tk.Label(
            contenedor,
            text=item["pregunta"],
            bg=CARD_BG,
            fg=NAVY_DARK,
            font=("Segoe UI", 22, "bold"),
            justify="left",
            anchor="w"
        )
        titulo.pack(fill="x", padx=22, pady=(20, 14))

        sub1 = tk.Label(
            contenedor,
            text="Archivos, funciones y responsabilidades",
            bg=CARD_BG,
            fg="#234B6C",
            font=("Segoe UI", 18, "bold")
        )
        sub1.pack(anchor="w", padx=22, pady=(4, 10))

        for archivo, funciones in item["archivos"]:
            bloque = tk.Frame(
                contenedor,
                bg="#F5F8FB",
                highlightbackground="#C8D2DC",
                highlightthickness=1
            )
            bloque.pack(fill="x", padx=22, pady=6)

            tk.Label(
                bloque,
                text=archivo,
                bg="#F5F8FB",
                fg=NAVY_DARK,
                font=("Consolas", 15, "bold"),
                anchor="w",
                justify="left"
            ).pack(anchor="w", padx=16, pady=(14, 8))

            for funcion, descripcion in funciones:
                linea = tk.Frame(bloque, bg="#F5F8FB")
                linea.pack(fill="x", padx=18, pady=4)

                tk.Label(
                    linea,
                    text="•  " + funcion,
                    bg="#F5F8FB",
                    fg="black",
                    font=("Segoe UI", 15, "bold"),
                    justify="left",
                    anchor="w"
                ).pack(anchor="w")

                tk.Label(
                    linea,
                    text=descripcion,
                    bg="#F5F8FB",
                    fg=TEXT,
                    font=("Segoe UI", 15),
                    wraplength=1050,
                    justify="left",
                    anchor="w"
                ).pack(anchor="w", padx=(24, 0), pady=(2, 2))

        sub2 = tk.Label(
            contenedor,
            text="Fragmentos representativos del código",
            bg=CARD_BG,
            fg="#234B6C",
            font=("Segoe UI", 18, "bold")
        )
        sub2.pack(anchor="w", padx=22, pady=(18, 10))

        for titulo_codigo, fragmento in item["codigos"]:
            tk.Label(
                contenedor,
                text=titulo_codigo,
                bg=CARD_BG,
                fg=NAVY_DARK,
                font=("Segoe UI", 16, "bold"),
                justify="left",
                anchor="w"
            ).pack(fill="x", padx=22, pady=(8, 6))

            marco_codigo = tk.Frame(
                contenedor,
                bg=CODE_BG,
                highlightbackground="black",
                highlightthickness=2
            )
            marco_codigo.pack(fill="x", padx=22, pady=(0, 10))

            tk.Label(
                marco_codigo,
                text=fragmento,
                bg=CODE_BG,
                fg="black",
                font=("Consolas", 14),
                justify="left",
                anchor="w"
            ).pack(fill="x", padx=16, pady=14)

        tk.Label(
            contenedor,
            text="Extractos resumidos del proyecto. Algunos bloques pueden omitir líneas intermedias.",
            bg=CARD_BG,
            fg="#6B7E90",
            font=("Segoe UI", 13, "italic"),
            justify="left"
        ).pack(anchor="w", padx=22, pady=(8, 24))

        self.scroll_contenido_indice.reset_top()

    def _construir_tab_sql(self):
        marco = tk.Frame(
            self.tab_sql,
            bg=CARD_BG,
            highlightbackground=NAVY,
            highlightthickness=2
        )
        marco.pack(fill="both", expand=True, padx=14, pady=14)

        tk.Label(
            marco,
            text="Consultas SQL de apoyo",
            bg=CARD_BG,
            fg=NAVY_DARK,
            font=("Segoe UI", 24, "bold")
        ).pack(anchor="w", padx=20, pady=(18, 10))

        scroll = ScrollableFrame(marco, bg=CARD_BG)
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        for titulo, sql in CONSULTAS_SQL:
            tk.Label(
                scroll.inner,
                text=titulo,
                bg=CARD_BG,
                fg=NAVY_DARK,
                font=("Segoe UI", 18, "bold")
            ).pack(anchor="w", padx=8, pady=(12, 6))

            bloque = tk.Frame(
                scroll.inner,
                bg=CODE_BG,
                highlightbackground="black",
                highlightthickness=2
            )
            bloque.pack(fill="x", padx=8, pady=(0, 8))

            tk.Label(
                bloque,
                text=sql,
                bg=CODE_BG,
                fg="black",
                font=("Consolas", 14),
                justify="left",
                anchor="w"
            ).pack(fill="x", padx=16, pady=14)

            self._crear_boton_copiar(scroll.inner, sql).pack(anchor="e", padx=8, pady=(0, 10))

    def _construir_tab_consola(self):
        marco = tk.Frame(
            self.tab_consola,
            bg=CARD_BG,
            highlightbackground=NAVY,
            highlightthickness=2
        )
        marco.pack(fill="both", expand=True, padx=14, pady=14)

        tk.Label(
            marco,
            text="Consola app.py",
            bg=CARD_BG,
            fg=NAVY_DARK,
            font=("Segoe UI", 24, "bold")
        ).pack(anchor="w", padx=20, pady=(18, 10))

        scroll = ScrollableFrame(marco, bg=CARD_BG)
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        for titulo, contenido in CONSOLA_APP:
            tk.Label(
                scroll.inner,
                text=titulo,
                bg=CARD_BG,
                fg=NAVY_DARK,
                font=("Segoe UI", 18, "bold")
            ).pack(anchor="w", padx=8, pady=(12, 6))

            bloque = tk.Frame(
                scroll.inner,
                bg=CODE_BG,
                highlightbackground="black",
                highlightthickness=2
            )
            bloque.pack(fill="x", padx=8, pady=(0, 8))

            tk.Label(
                bloque,
                text=contenido,
                bg=CODE_BG,
                fg="black",
                font=("Consolas", 14),
                justify="left",
                anchor="w"
            ).pack(fill="x", padx=16, pady=14)

            self._crear_boton_copiar(scroll.inner, contenido).pack(anchor="e", padx=8, pady=(0, 10))


if __name__ == "__main__":
    app = ExposicionApp()
    app.mainloop()
