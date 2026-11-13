
import re

from motor_ia.interpretar_consulta import (
    preparar_clasificador,
    interpretar_pregunta
)

from motor_ia.entidades import (
    conectar_bd,
    normalizar_texto,
    cargar_instituciones,
    cargar_programas
)

from motor_ia.contexto import (
    crear_contexto,
    actualizar_contexto,
    mostrar_contexto,
    es_seguimiento,
    es_seguimiento_estructurado
)

from funciones.buscar_programa import buscar_programa
from funciones.buscar_institucion import buscar_institucion
from funciones.filtrar_modalidad import filtrar_modalidad
from sentence_transformers import SentenceTransformer

from motor_ia.busqueda_semantica import (
    cargar_programas as cargar_programas_semanticos,
    buscar_semanticamente,
    RUTA_MODELO
)

from motor_ia.recuperacion_semantica import recuperar_ofertas
from motor_ia.validacion_respuestas import validar_consulta
from motor_ia.interaccion_general import detectar_interaccion_general
from motor_ia.validacion_cobertura_tematica import (
    construir_indice,
    comprobar_cobertura,
    es_exploracion_tematica,
    detectar_temas
)
from motor_ia.afinidades_academicas import buscar_afinidades
from motor_ia.interpretar_modalidades import (
    analizar_modalidades,
    mensaje_aclaracion_modalidad,
    ajustar_interpretacion,
)
from motor_ia.generador_respuestas import (
    respuesta_sin_cobertura,
    respuesta_afinidades,
    respuesta_programas,
    respuesta_ofertas,
)

# activar para observar las intenciones y puntuaciones durante el desarrollo.
MODO_DIAGNOSTICO = False


def filtrar_ofertas_combinadas(ofertas, institucion=None, modalidad=None):
    """Aplica conjuntamente los filtros solicitados a ofertas verificadas."""
    return [
        oferta for oferta in ofertas
        if (institucion is None or oferta["institucion"] == institucion["nombre"])
        and (modalidad is None or oferta["modalidad"] == modalidad)
    ]


def seleccionar_programas_de_institucion(conexion, programas, institucion, modalidad=None):
    """Conserva solo programas con ofertas de la institución y modalidad indicadas."""
    seleccionados = []
    for id_programa, nombre in programas:
        ofertas = buscar_programa(conexion, id_programa=id_programa)
        if filtrar_ofertas_combinadas(ofertas, institucion, modalidad):
            seleccionados.append((id_programa, nombre))
    return seleccionados


SIGLAS_INSTITUCIONALES = {
    "itam": "INSTITUTO TECNOLÓGICO AUTÓNOMO DE MÉXICO",
    "uvm": "UNIVERSIDAD DEL VALLE DE MÉXICO",
    "unam": "UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICO",
}


def identificar_sigla_institucional(pregunta):
    """Detecta siglas institucionales completas en una pregunta."""
    texto = normalizar_texto(pregunta)
    for sigla in SIGLAS_INSTITUCIONALES:
        if re.search(rf"\b{re.escape(sigla)}\b", texto):
            return sigla
    return None


def resolver_institucion_mencionada(pregunta, institucion, instituciones):
    """Relaciona siglas con instituciones existentes en el catálogo."""
    if institucion is not None:
        return institucion

    sigla = identificar_sigla_institucional(pregunta)
    if sigla is None:
        return None

    nombre_objetivo = normalizar_texto(SIGLAS_INSTITUCIONALES[sigla])
    for candidata in instituciones:
        if isinstance(candidata, dict):
            identificador = candidata.get("id_institucion")
            nombre = candidata.get("nombre")
        elif isinstance(candidata, (tuple, list)) and len(candidata) >= 2:
            identificador, nombre = candidata[:2]
        else:
            continue
        if nombre is not None and normalizar_texto(str(nombre)) == nombre_objetivo:
            return {"id_institucion": identificador, "nombre": nombre}
    return None


def mensaje_sigla_sin_registro(pregunta, institucion):
    """Aclara la ausencia de una institución conocida en el alcance disponible."""
    if institucion is not None:
        return None
    sigla = identificar_sigla_institucional(pregunta)
    if sigla is None:
        return None
    nombre = SIGLAS_INSTITUCIONALES[sigla]
    return (
        f"Reconocí {sigla.upper()} ({nombre}), pero no encontré esa institución "
        "en el catálogo incorporado de registros SEP de abril de 2021. "
        "Esto no significa que la universidad no ofrezca licenciaturas: "
        "la fuente consultada tiene una cobertura limitada. "
        "No puedo mostrar carreras de esa institución sin registros verificables."
    )


def conservar_seguimiento_academico(pregunta, interpretacion, contexto):
    """Restringe referencias a búsquedas previas sin heredar temas independientes.

    Una nueva carrera explícita siempre inicia otra búsqueda, salvo las
    referencias nominales 'esa carrera' que vinculan la institución indicada.
    """
    if es_seguimiento(pregunta):
        return True
    texto = normalizar_texto(pregunta)
    if texto.startswith(("dejemos", "olvidemos", "cambiemos", "cambiando de tema")):
        return False
    if interpretacion.get("programa") is not None:
        return False
    if detectar_temas(pregunta):
        return False
    if interpretacion.get("institucion") is not None:
        return False
    tiene_antecedente = (
        contexto["institucion"] is not None
        or contexto["programa"] is not None
        or bool(contexto["programas_semanticos"])
    )
    return tiene_antecedente and interpretacion.get("modalidad") is not None


def es_peticion_exploratoria_explicita(pregunta):
    """Distingue una exploración por área de una búsqueda de título exacto.

    Solo se aplican expresiones explícitas de exploración. La presencia de
    una especialidad en un nombre de programa no basta para activar MiniLM.
    """
    texto = normalizar_texto(pregunta)
    return bool(re.search(
        r"\b(?:algo relacionado con|carreras? relacionadas? con|"
        r"programas? relacionados? con|opciones? relacionadas? con|"
        r"algo que tenga que ver con|areas? relacionadas? con)\b",
        texto,
    ))



# busquedas amplias v1
def buscar_categoria_general(pregunta, interpretacion, conexion, programas):
    """Busca nombres de programas por categoría, sin inferir especialidades."""
    if interpretacion.get('programa') is not None:
        return None

    texto = normalizar_texto(pregunta)
    if re.search(r"\bingenierias?\b", texto):
        categoria = 'ingenierías'
        patron = re.compile(r"\bingenieria\b")
    elif re.search(r"\bidiomas?\b", texto):
        categoria = 'idiomas'
        patron = re.compile(r"\bidiomas\b")
    else:
        return None

    ids = [int(id_programa) for id_programa, nombre in programas
           if patron.search(normalizar_texto(nombre))]
    if not ids:
        return {'categoria': categoria, 'ofertas': [], 'ids': []}

    modalidad = interpretacion.get('modalidad')
    institucion = interpretacion.get('institucion')
    id_institucion = (institucion['id_institucion'] if institucion else None)
    sql = """
        SELECT i.nombre AS institucion,
               pa.nombre AS programa,
               p.nombre AS plantel,
               m.nombre AS modalidad
        FROM catalogo.oferta_educativa o
        JOIN catalogo.programa_academico pa ON pa.id_programa = o.id_programa
        JOIN catalogo.plantel p ON p.id_plantel = o.id_plantel
        JOIN catalogo.institucion i ON i.id_institucion = p.id_institucion
        JOIN catalogo.modalidad m ON m.id_modalidad = o.id_modalidad
        WHERE o.id_programa = ANY(%s)
          AND (%s IS NULL OR m.nombre = %s)
          AND (%s IS NULL OR i.id_institucion = %s)
        ORDER BY pa.nombre, i.nombre, p.nombre NULLS LAST
    """
    with conexion.cursor() as cursor:
        cursor.execute(sql, (ids, modalidad, modalidad, id_institucion, id_institucion))
        columnas = [c[0] for c in cursor.description]
        ofertas = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
    return {'categoria': categoria, 'ofertas': ofertas, 'ids': ids}


# catalogo general v6
def es_consulta_catalogo_general(pregunta, interpretacion):
    texto = normalizar_texto(pregunta)

    if any(interpretacion.get(c) is not None for c in
           ("institucion", "programa", "modalidad")):
        return False

    if detectar_temas(pregunta):
        return False

    if re.search(
        r"\b(?:ingenierias?|idiomas?|universidad|institucion|instituto|escuela|plantel)\b",
        texto
    ):
        return False

    if not re.search(
        r"\b(?:licenciaturas?|carreras?|programas?|areas?)\b",
        texto
    ):
        return False

    return bool(re.search(
        r"\b(?:que|cuales|cuantas|muestrame|mostrar|muestra|lista|listado|catalogo|todas?|disponibles|puedo|ofrecen|hay|existen)\b",
        texto
    ))

class MotorEducativo:
    """Servicio único para consola e interfaz de escritorio.

    Los mensajes de respuesta proceden de las funciones existentes del proyecto;
    la presentación no necesita interpretar el texto impreso por PowerShell.
    """

    def __init__(self, contrasena=None):
        from contextlib import nullcontext
        from unittest.mock import patch
        self.modelo = preparar_clasificador()
        if contrasena is None:
            self.conexion = conectar_bd()
        else:
            # Se inyecta la clave solo durante la conexión; no se persiste aquí.
            # Compatible tanto con `import getpass` como con
            # `from getpass import getpass` dentro del módulo de conexión.
            simbolo = conectar_bd.__globals__.get('getpass')
            sustitucion = (
                patch.dict(conectar_bd.__globals__, {'getpass': lambda *_a, **_k: contrasena})
                if callable(simbolo) else nullcontext()
            )
            with patch('getpass.getpass', return_value=contrasena), sustitucion:
                self.conexion = conectar_bd()
        try:
            self.instituciones = cargar_instituciones(self.conexion)
            self.programas = cargar_programas(self.conexion)
            self.modelo_semantico = SentenceTransformer(str(RUTA_MODELO))
            self.programas_semanticos = cargar_programas_semanticos(self.conexion)
            nombres = [nombre for _, nombre in self.programas_semanticos]
            self.vectores_semanticos = self.modelo_semantico.encode(
                nombres, convert_to_tensor=True, show_progress_bar=False
            )
            self.indice_tematico = construir_indice(self.programas_semanticos)
            self.contexto = crear_contexto()
            self.opciones_pendientes = None
            # PAGINACION_OFERTAS_V1
            self._pag_ofertas = None
            self._pag_contexto = None
            self._pag_busqueda = 0
        except Exception:
            self.conexion.close()
            raise

    def cerrar(self):
        if self.conexion is not None:
            self.conexion.close()
            self.conexion = None

    # paginacion
    def _respuesta_ofertas_paginada(self, ofertas, contexto):
        """Retiene los registros de la búsqueda y conserva el formato original."""
        self._pag_ofertas = list(ofertas)
        self._pag_contexto = dict(contexto)
        return respuesta_ofertas(ofertas, contexto)


    
    def _preparar_catalogo_general(self):
        from collections import defaultdict
        from motor_ia.descripciones_tematicas import describir_por_nombre
        from motor_ia.afinidades_academicas import NOMBRES_AREAS

        grupos = defaultdict(list)
        etiquetas_adicionales = {
            "administracion": "Administraci\u00f3n",
            "animacion": "Animaci\u00f3n",
            "arquitectura": "Arquitectura",
            "derecho": "Derecho",
            "gastronomia": "Gastronom\u00eda",
            "medicina": "Medicina y enfermer\u00eda",
            "psicologia": "Psicolog\u00eda",
            "turismo": "Turismo",
            "videojuegos": "Videojuegos",
        }

        otras = "Sin \u00e1rea identificable por el nombre"

        for id_programa, nombre in self.programas_semanticos:
            _, etiquetas = describir_por_nombre(nombre)

            if etiquetas:
                area = etiquetas[0]
                titulo_area = NOMBRES_AREAS.get(
                    area, etiquetas_adicionales.get(
                        area, area.replace("_", " ").title()
                    )
                )
            else:
                titulo_area = otras

            grupos[titulo_area].append({
                "programa": nombre[3:] if nombre.startswith("EN ") else nombre,
                "area": titulo_area
            })

        nombres_areas = sorted(
            (a for a in grupos if a != otras),
            key=normalizar_texto
        )
        if otras in grupos:
            nombres_areas.append(otras)

        for registros in grupos.values():
            registros.sort(
                key=lambda fila: normalizar_texto(fila["programa"])
            )

        listado = []
        posicion = 0
        while True:
            incluidos = 0
            for area in nombres_areas:
                if posicion < len(grupos[area]):
                    listado.append(grupos[area][posicion])
                    incluidos += 1
            if not incluidos:
                break
            posicion += 1

        return listado

    def _texto_catalogo_general(self, pagina, datos):
        total = len(self._pag_ofertas or [])
        desde = (pagina - 1) * 6
        hasta = min(desde + 6, total)

        lineas = [
            f"Cat\u00e1logo general: {total} programas de licenciatura con ofertas en CDMX.",
            f"P\u00e1gina {pagina} de {datos['paginas']} | Carreras {desde + 1} a {hasta}.",
            "Las \u00e1reas son orientativas, inferidas del nombre; no son categor\u00edas oficiales de la SEP."
        ]

        for numero, fila in enumerate(
            self._pag_ofertas[desde:hasta], start=desde + 1
        ):
            lineas.append(
                f"{numero}. {fila['programa']} | "
                f"\u00c1rea orientativa: {fila['area']}"
            )

        lineas.append(
            "Fuente: registros SEP de abril de 2021; verifica su vigencia actual."
        )
        return "\n".join(lineas)

    def _datos_pagina(self, pagina):
        total = len(self._pag_ofertas or [])
        tamano = 6 if self._pag_contexto and self._pag_contexto.get('modo') == 'catalogo_general' else 15
        paginas = (total + tamano - 1) // tamano
        if paginas <= 1:
            return None
        if not isinstance(pagina, int) or isinstance(pagina, bool) or not (1 <= pagina <= paginas):
            return None
        return {'pagina': pagina, 'paginas': paginas, 'total': total,
                'busqueda': self._pag_busqueda}

    def obtener_pagina(self, solicitud):
        """Entrega otra página de la búsqueda actual sin acceder nuevamente a SQL."""
        if not isinstance(solicitud, dict) or solicitud.get('busqueda') != self._pag_busqueda:
            return {'mensaje': 'Esta búsqueda ya no está activa. Realiza otra consulta.',
                    'cerrar': False, 'tipo': 'respuesta'}
        pagina = solicitud.get('pagina')
        datos = self._datos_pagina(pagina)
        if datos is None:
            return {'mensaje': 'No existe esa página de resultados.',
                    'cerrar': False, 'tipo': 'respuesta'}
        if self._pag_contexto and self._pag_contexto.get('modo') == 'catalogo_general':
            return {'mensaje': self._texto_catalogo_general(pagina, datos),
                    'cerrar': False, 'tipo': 'respuesta', 'paginacion': datos}
        desde = (pagina - 1) * 15
        hasta = min(desde + 15, datos['total'])
        lineas = [f"Mostrando ofertas {desde + 1} a {hasta} de {datos['total']}."]
        for oferta in self._pag_ofertas[desde:hasta]:
            nombre = str(oferta['programa'])
            if nombre.startswith('EN '):
                nombre = nombre[3:]
            lineas.append(
                f"- {oferta['institucion']} | {nombre} | "
                f"{oferta.get('plantel') or 'Plantel no especificado'} | {oferta['modalidad']}"
            )
        lineas.append('Fuente: registros SEP de abril de 2021; verifica su vigencia actual.')
        return {'mensaje': '\n'.join(lineas), 'cerrar': False,
                'tipo': 'respuesta', 'paginacion': datos}

    def resolver_afinidades(self, solicitud):
        """Valida la confirmacion de alternativas."""
        if not isinstance(solicitud, dict):
            solicitud = {}

        busqueda = solicitud.get('busqueda')
        aceptar = solicitud.get('aceptar')

        vigente = (
            self.conexion is not None
            and isinstance(busqueda, int)
            and not isinstance(busqueda, bool)
            and busqueda == self._pag_busqueda
            and isinstance(aceptar, bool)
            and bool(self.opciones_pendientes)
            and bool(self.opciones_pendientes.get('candidatos'))
        )

        if not vigente:
            return {
                'mensaje': 'Esta propuesta ya no esta activa.',
                'cerrar': False,
                'tipo': 'respuesta'
            }

        return self.procesar('si' if aceptar else 'no')

    def procesar(self, pregunta):
        """Procesa un turno; retorna {mensaje, cerrar, tipo} conservando la sesión."""
        if self.conexion is None:
            raise RuntimeError('El motor ya está cerrado')
        pregunta = pregunta.strip()
        self._pag_busqueda += 1
        self._pag_ofertas = None
        self._pag_contexto = None
        if normalizar_texto(pregunta) == 'salir':
            return {'mensaje': 'Programa finalizado.', 'cerrar': True, 'tipo': 'salida'}
        if not pregunta:
            return {'mensaje': '', 'cerrar': False, 'tipo': 'vacio'}

        modelo = self.modelo
        conexion = self.conexion
        instituciones = self.instituciones
        programas = self.programas
        modelo_semantico = self.modelo_semantico
        programas_semanticos = self.programas_semanticos
        vectores_semanticos = self.vectores_semanticos
        indice_tematico = self.indice_tematico
        contexto = self.contexto
        opciones_pendientes = self.opciones_pendientes
        mensajes = []

        def registrar(*partes, sep=' ', end='\n'):
            mensajes.append(sep.join(map(str, partes)) + end)

        def finalizar(cerrar=False):
            self.contexto = contexto
            self.opciones_pendientes = opciones_pendientes
            mensaje = ''.join(mensajes).strip()
            resultado = {'mensaje': mensaje, 'cerrar': cerrar,
                         'tipo': 'respuesta' if mensaje else 'vacio'}
            datos = self._datos_pagina(1)
            if datos is not None:
                resultado['paginacion'] = datos
            if not cerrar and opciones_pendientes and opciones_pendientes.get('candidatos'):
                resultado['afinidades'] = {
                    'busqueda': self._pag_busqueda,
                    'cantidad': len(opciones_pendientes['candidatos'])
                }
            return resultado

        if opciones_pendientes is not None:
            respuesta = normalizar_texto(pregunta)
            afirmaciones = {'si', 'si por favor', 'claro', 'adelante', 'por supuesto', 'muestrame las opciones', 'muestrame las afines', 'quiero ver las afines', 'busca opciones afines', 'si muestrame', 'si muestrame las opciones'}
            negativas = {'no', 'no gracias', 'mejor no', 'cancelar'}
            if respuesta in afirmaciones:
                pendientes = opciones_pendientes
                opciones_pendientes = None
                resultados_afines = []
                for candidato in pendientes['candidatos']:
                    ofertas = buscar_programa(conexion, id_programa=candidato['id_programa'])
                    ofertas = filtrar_ofertas_combinadas(ofertas, pendientes.get('institucion'), pendientes.get('modalidad'))
                    if ofertas:
                        resultados_afines.append({**candidato, 'ofertas': ofertas})
                contexto = crear_contexto()
                contexto['institucion'] = pendientes.get('institucion')
                contexto['modalidad'] = pendientes.get('modalidad')
                contexto['programas_semanticos'] = [r['id_programa'] for r in resultados_afines]
                registrar('\n' + respuesta_afinidades(resultados_afines, pendientes['temas']))
                return finalizar()
            if respuesta in negativas:
                opciones_pendientes = None
                registrar('\nDe acuerdo. ¿Qué otro tema académico te interesa?')
                return finalizar()
            opciones_pendientes = None
        interaccion = detectar_interaccion_general(pregunta)
        if interaccion is not None:
            registrar('\n' + interaccion['mensaje'])
            if interaccion['cerrar']:
                registrar('Programa finalizado.')
                return finalizar(cerrar=True)
            return finalizar()
        interpretacion = interpretar_pregunta(pregunta, modelo, instituciones, programas)
        interpretacion['institucion'] = resolver_institucion_mencionada(pregunta, interpretacion.get('institucion'), instituciones)
        aviso_sigla = mensaje_sigla_sin_registro(pregunta, interpretacion['institucion'])
        if aviso_sigla is not None:
            contexto = crear_contexto()
            opciones_pendientes = None
            registrar('\n' + aviso_sigla)
            return finalizar()
        analisis_modalidad = analizar_modalidades(pregunta)
        aclaracion_modalidad = mensaje_aclaracion_modalidad(analisis_modalidad)
        if aclaracion_modalidad is not None:
            registrar('\n' + aclaracion_modalidad)
            return finalizar()
        interpretacion = ajustar_interpretacion(interpretacion, analisis_modalidad, tiene_tema=bool(detectar_temas(pregunta)))
        if es_consulta_catalogo_general(pregunta, interpretacion):
            self._pag_ofertas = self._preparar_catalogo_general()
            self._pag_contexto = {"modo": "catalogo_general"}
            contexto = crear_contexto()
            opciones_pendientes = None

            if self._pag_ofertas:
                datos = self._datos_pagina(1)
                if datos is None:
                    datos = {
                        "pagina": 1,
                        "paginas": 1,
                        "total": len(self._pag_ofertas),
                        "busqueda": self._pag_busqueda
                    }
                registrar(self._texto_catalogo_general(1, datos))
            else:
                registrar(
                    "No se encontraron programas con ofertas en el cat\u00e1logo consultado."
                )
            return finalizar()
        if MODO_DIAGNOSTICO:
            registrar('\nIntencion:', interpretacion['intencion'])
            registrar('Confianza:', f"{interpretacion['confianza']:.2%}")
        seguimiento_academico = conservar_seguimiento_academico(pregunta, interpretacion, contexto)
        if seguimiento_academico and contexto['programas_semanticos']:
            nuevo_contexto = actualizar_contexto(contexto, interpretacion, conservar=seguimiento_academico)
            nuevo_contexto['programas_semanticos'] = list(contexto['programas_semanticos'])
            if nuevo_contexto['institucion'] is None and contexto['institucion'] is not None:
                nuevo_contexto['institucion'] = contexto['institucion']
            modalidad = nuevo_contexto['modalidad']
            institucion = nuevo_contexto['institucion']
            if modalidad is None:
                registrar('\n¿Quieres ver las opciones mixtas, escolarizadas o no escolarizadas?')
                return finalizar()
            resultados = []
            for id_programa in nuevo_contexto['programas_semanticos']:
                ofertas = buscar_programa(conexion, id_programa=id_programa, modalidad=modalidad)
                if institucion is not None:
                    ofertas = [oferta for oferta in ofertas if oferta['institucion'] == institucion['nombre']]
                resultados.extend(ofertas)
            contexto = nuevo_contexto
            if MODO_DIAGNOSTICO:
                mostrar_contexto(contexto)
            registrar('\n' + self._respuesta_ofertas_paginada(resultados, contexto))
            return finalizar()
        # busquedas amplias v1 categorias generales y singular o plural.
        busqueda_amplia = buscar_categoria_general(
            pregunta, interpretacion, conexion, programas
        )
        if busqueda_amplia is not None:
            contexto = crear_contexto()
            contexto['modalidad'] = interpretacion.get('modalidad')
            contexto['institucion'] = interpretacion.get('institucion')
            ofertas_amplias = busqueda_amplia['ofertas']
            if ofertas_amplias:
                registrar('\nBúsqueda amplia por categoría: ' + busqueda_amplia['categoria'] + '.')
                registrar(self._respuesta_ofertas_paginada(ofertas_amplias, contexto))
                if busqueda_amplia['categoria'] == 'idiomas':
                    registrar('El nombre del programa no confirma qué lenguas específicas se imparten; consulta esa información con la institución.')
            else:
                registrar('\nNo encontré ofertas registradas para esa categoría con los filtros solicitados.')
            return finalizar()
        seguimiento_estructurado = es_seguimiento_estructurado(pregunta, contexto) or (seguimiento_academico and (not contexto['programas_semanticos']) and (contexto['institucion'] is not None or contexto['programa'] is not None) and (interpretacion.get('programa') is None))
        hay_tema = bool(detectar_temas(pregunta))
        exploracion_explicita = hay_tema and es_peticion_exploratoria_explicita(pregunta) and (not seguimiento_estructurado)
        consulta_combinada = hay_tema and interpretacion.get('institucion') is not None and (interpretacion.get('programa') is None or exploracion_explicita) and (not seguimiento_estructurado)
        explorar_tema = False if seguimiento_estructurado else exploracion_explicita or consulta_combinada or es_exploracion_tematica(interpretacion)
        if not explorar_tema and (not seguimiento_estructurado):
            mensaje_aclaracion = validar_consulta(interpretacion)
            if mensaje_aclaracion is not None:
                registrar('\n' + mensaje_aclaracion)
                return finalizar()
        if explorar_tema:
            institucion_pedida = interpretacion.get('institucion')
            modalidad_pedida = interpretacion.get('modalidad')
            cobertura = comprobar_cobertura(pregunta, indice_tematico)
            if cobertura['estado'] != 'cobertura_directa':
                contexto = crear_contexto()
                if cobertura['estado'] == 'sin_cobertura_directa':
                    temas = cobertura['temas_prioritarios']
                    if institucion_pedida is not None or modalidad_pedida is not None:
                        todas_afines = buscar_afinidades(temas, programas_semanticos, limite=len(programas_semanticos))
                        afines = []
                        for candidato in todas_afines:
                            ofertas = buscar_programa(conexion, id_programa=candidato['id_programa'])
                            if filtrar_ofertas_combinadas(ofertas, institucion_pedida, modalidad_pedida):
                                afines.append(candidato)
                                if len(afines) == 5:
                                    break
                    else:
                        afines = buscar_afinidades(temas, programas_semanticos, limite=5)
                    opciones_pendientes = {'temas': temas, 'candidatos': afines, 'institucion': institucion_pedida, 'modalidad': modalidad_pedida} if afines else None
                    registrar('\n' + respuesta_sin_cobertura(temas, bool(afines)))
                    if institucion_pedida is not None:
                        registrar('La búsqueda de alternativas se restringe a ' + institucion_pedida['nombre'] + '.')
                else:
                    opciones_pendientes = None
                    registrar('\n' + cobertura['mensaje'])
                return finalizar()
            indices_permitidos = [i for i, (id_programa, _) in enumerate(programas_semanticos) if id_programa in cobertura['ids_validos']]
            programas_permitidos = [programas_semanticos[i] for i in indices_permitidos]
            if institucion_pedida is not None:
                programas_permitidos = seleccionar_programas_de_institucion(conexion, programas_permitidos, institucion_pedida, modalidad_pedida)
                ids_permitidos = {pid for pid, _ in programas_permitidos}
                indices_permitidos = [i for i in indices_permitidos if programas_semanticos[i][0] in ids_permitidos]
            if not programas_permitidos:
                contexto = crear_contexto()
                opciones_pendientes = None
                registrar('\nNo encontré programas con cobertura temática directa que cumplan los filtros de institución y modalidad en el catálogo consultado.')
                return finalizar()
            vectores_permitidos = vectores_semanticos[indices_permitidos]
            candidatos = buscar_semanticamente(pregunta, modelo_semantico, programas_permitidos, vectores_permitidos, limite=5)
            resultados_semanticos = recuperar_ofertas(conexion, candidatos)
            if modalidad_pedida is not None or institucion_pedida is not None:
                for resultado in resultados_semanticos:
                    resultado['ofertas'] = filtrar_ofertas_combinadas(resultado['ofertas'], institucion_pedida, modalidad_pedida)
                    resultado['total_ofertas'] = len(resultado['ofertas'])
                resultados_semanticos = [resultado for resultado in resultados_semanticos if resultado['ofertas']]
            registrar('\n' + respuesta_programas(resultados_semanticos, cobertura['temas_prioritarios']))
            contexto = crear_contexto()
            contexto['institucion'] = institucion_pedida
            contexto['modalidad'] = modalidad_pedida
            contexto['programas_semanticos'] = [resultado['id_programa'] for resultado in resultados_semanticos if resultado['ofertas']]
            return finalizar()
        nuevo_contexto = actualizar_contexto(contexto, interpretacion, conservar=seguimiento_academico)
        if MODO_DIAGNOSTICO:
            mostrar_contexto(nuevo_contexto)
        institucion = nuevo_contexto['institucion']
        programa = nuevo_contexto['programa']
        modalidad = nuevo_contexto['modalidad']
        if programa is not None:
            resultados = buscar_programa(conexion, id_programa=programa['id_programa'], modalidad=modalidad)
            if institucion is not None:
                resultados = [oferta for oferta in resultados if oferta['institucion'] == institucion['nombre']]
        elif institucion is not None:
            resultados = buscar_institucion(conexion, id_institucion=institucion['id_institucion'], modalidad=modalidad)
        elif modalidad is not None:
            resultados = filtrar_modalidad(conexion, modalidad=modalidad)
        else:
            registrar('\nNo se identificaron filtros suficientes para realizar la busqueda.')
            return finalizar()
        contexto = nuevo_contexto
        registrar('\n' + self._respuesta_ofertas_paginada(resultados, contexto))
        return finalizar()

def main():
    print('=' * 60)
    print('OFERTA EDUCATIVA CIUDAD DE MEXICO 2.0')
    print('Integracion: IA, PostgreSQL y contexto conversacional')
    print('=' * 60)
    motor = MotorEducativo()
    try:
        print('\nMotor semantico preparado.\n\nSistema preparado.')
        while True:
            pregunta = input("\nEscribe tu pregunta (o 'salir'): ").strip()
            if not pregunta:
                continue
            resultado = motor.procesar(pregunta)
            if resultado['mensaje']:
                print('\n' + resultado['mensaje'])
            if resultado['cerrar']:
                if pregunta.lower() != 'salir':
                    print('Programa finalizado.')
                break
    finally:
        motor.cerrar()


if __name__ == '__main__':
    main()
