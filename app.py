
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

# Activar para observar las intenciones y puntuaciones durante el desarrollo.
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


def resolver_institucion_mencionada(pregunta, institucion, instituciones):
    """Resuelve ITAM utilizando el formato real (id, nombre) del catálogo.

    La extracción de entidades del resto de la aplicación utiliza diccionarios
    con las claves 'id_institucion' y 'nombre'.
    """
    if institucion is not None:
        return institucion
    if not re.search(r"\bitam\b", normalizar_texto(pregunta)):
        return None

    objetivo = "instituto tecnologico autonomo de mexico"
    for candidata in instituciones:
        if isinstance(candidata, dict):
            id_institucion = candidata.get("id_institucion")
            nombre = candidata.get("nombre")
        elif isinstance(candidata, (tuple, list)) and len(candidata) >= 2:
            id_institucion, nombre = candidata[0], candidata[1]
        else:
            continue
        if nombre is not None and normalizar_texto(str(nombre)) == objetivo:
            return {"id_institucion": id_institucion, "nombre": nombre}
    return None


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


def main():
    print("=" * 60)
    print("OFERTA EDUCATIVA CIUDAD DE MEXICO 2.0")
    print("Integracion: IA, PostgreSQL y contexto conversacional")
    print("=" * 60)

    modelo = preparar_clasificador()

    with conectar_bd() as conexion:
        instituciones = cargar_instituciones(conexion)
        programas = cargar_programas(conexion)
        # Preparar la busqueda semantica.
        modelo_semantico = SentenceTransformer(str(RUTA_MODELO))

        programas_semanticos = cargar_programas_semanticos(conexion)

        nombres_semanticos = [
            nombre for id_programa, nombre in programas_semanticos
        ]

        vectores_semanticos = modelo_semantico.encode(
            nombres_semanticos,
            convert_to_tensor=True,
            show_progress_bar=True
        )

        # Crear el indice de temas una sola vez a partir del catalogo.
        indice_tematico = construir_indice(programas_semanticos)
        print("Motor semantico preparado.")

        # Crear una memoria para la sesion actual.
        contexto = crear_contexto()
        # Alternativas afines preparadas para una confirmacion (si/no).
        opciones_pendientes = None

        print("\nSistema preparado.")

        while True:
            pregunta = input(
                "\nEscribe tu pregunta (o 'salir'): "
            ).strip()

            if normalizar_texto(pregunta) == "salir":
                print("Programa finalizado.")
                break

            if not pregunta:
                continue

            # La solicitud de afines solo se ofrece tras verificar que existen
            # nombres de programas relacionados de manera indirecta en la BD.
            if opciones_pendientes is not None:
                respuesta = normalizar_texto(pregunta)
                afirmaciones = {
                    "si", "si por favor", "claro", "adelante", "por supuesto",
                    "muestrame las opciones", "muestrame las afines",
                    "quiero ver las afines", "busca opciones afines",
                    "si muestrame", "si muestrame las opciones",
                }
                negativas = {"no", "no gracias", "mejor no", "cancelar"}

                if respuesta in afirmaciones:
                    pendientes = opciones_pendientes
                    opciones_pendientes = None
                    resultados_afines = []
                    for candidato in pendientes["candidatos"]:
                        ofertas = buscar_programa(
                            conexion,
                            id_programa=candidato["id_programa"]
                        )
                        ofertas = filtrar_ofertas_combinadas(
                            ofertas, pendientes.get("institucion"),
                            pendientes.get("modalidad")
                        )
                        if ofertas:
                            resultados_afines.append({**candidato, "ofertas": ofertas})
                    contexto = crear_contexto()
                    contexto["institucion"] = pendientes.get("institucion")
                    contexto["modalidad"] = pendientes.get("modalidad")
                    contexto["programas_semanticos"] = [
                        r["id_programa"] for r in resultados_afines
                    ]
                    print("\n" + respuesta_afinidades(
                        resultados_afines, pendientes["temas"]
                    ))
                    continue

                if respuesta in negativas:
                    opciones_pendientes = None
                    print("\nDe acuerdo. ¿Qué otro tema académico te interesa?")
                    continue

                # Otra consulta inicia un tema independiente.
                opciones_pendientes = None

            # Interacciones generales y datos fuera del alcance. Se comprueban
            # antes del clasificador para evitar búsquedas irrelevantes.
            interaccion = detectar_interaccion_general(pregunta)
            if interaccion is not None:
                print("\n" + interaccion["mensaje"])
                if interaccion["cerrar"]:
                    print("Programa finalizado.")
                    break
                # Una cortesía o solicitud general no borra el contexto vigente.
                continue

            # Interpretar la pregunta utilizando el motor de IA.
            interpretacion = interpretar_pregunta(
                pregunta,
                modelo,
                instituciones,
                programas
            )

            # Resolver siglas institucionales comunes contra entidades reales.
            interpretacion["institucion"] = resolver_institucion_mencionada(
                pregunta, interpretacion.get("institucion"), instituciones
            )

            # Reconocer modalidades expresadas en lenguaje natural,
            # incluso si el clasificador eligió una intención distinta.
            analisis_modalidad = analizar_modalidades(pregunta)
            aclaracion_modalidad = mensaje_aclaracion_modalidad(analisis_modalidad)
            if aclaracion_modalidad is not None:
                print("\n" + aclaracion_modalidad)
                continue

            interpretacion = ajustar_interpretacion(
                interpretacion,
                analisis_modalidad,
                tiene_tema=bool(detectar_temas(pregunta)),
            )

            if MODO_DIAGNOSTICO:
                print("\nIntencion:", interpretacion["intencion"])
                print("Confianza:", f'{interpretacion["confianza"]:.2%}')
            # Los cambios de modalidad reutilizan la búsqueda original,
            # incluso si el filtro previo no produjo ninguna oferta.
            seguimiento_academico = conservar_seguimiento_academico(
                pregunta, interpretacion, contexto
            )
            if seguimiento_academico and contexto["programas_semanticos"]:
                nuevo_contexto = actualizar_contexto(
                    contexto, interpretacion, conservar=seguimiento_academico
                )
                # La referencia semántica conserva los programas originales.
                nuevo_contexto["programas_semanticos"] = list(contexto["programas_semanticos"])
                if nuevo_contexto["institucion"] is None and contexto["institucion"] is not None:
                    nuevo_contexto["institucion"] = contexto["institucion"]
                modalidad = nuevo_contexto["modalidad"]
                institucion = nuevo_contexto["institucion"]

                if modalidad is None:
                    print("\n¿Quieres ver las opciones mixtas, escolarizadas o no escolarizadas?")
                    continue

                resultados = []
                for id_programa in nuevo_contexto["programas_semanticos"]:
                    ofertas = buscar_programa(
                        conexion,
                        id_programa=id_programa,
                        modalidad=modalidad
                    )
                    if institucion is not None:
                        ofertas = [
                            oferta for oferta in ofertas
                            if oferta["institucion"] == institucion["nombre"]
                        ]
                    resultados.extend(ofertas)

                contexto = nuevo_contexto
                if MODO_DIAGNOSTICO:
                    mostrar_contexto(contexto)
                print("\n" + respuesta_ofertas(resultados, contexto))
                continue

            # Una referencia como "esa licenciatura" conserva el programa y la
            # institucion anteriores, aunque el clasificador no los extraiga
            # de nuevo. No debe entrar a exploracion tematica ni perderse en
            # la validacion de una consulta aislada.
            seguimiento_estructurado = es_seguimiento_estructurado(
                pregunta, contexto
            ) or (
                seguimiento_academico
                and not contexto["programas_semanticos"]
                and (contexto["institucion"] is not None
                     or contexto["programa"] is not None)
                and interpretacion.get("programa") is None
            )

            # Distinguir búsquedas por intereses de filtros de modalidad.
            # Si hay un seguimiento estructurado, conservamos la consulta
            # anterior en lugar de reencaminarla a MiniLM.
            # Una institución explícita no debe anular el interés temático.
            # Se prioriza el programa exacto cuando también fue reconocido.
            hay_tema = bool(detectar_temas(pregunta))
            # En preguntas exploratorias como "algo relacionado con ciencia de
            # datos", el extractor puede encontrar el título exacto CIENCIA DE
            # DATOS aunque también exista INGENIERÍA EN CIENCIA DE DATOS.
            # Una petición explícita de exploración debe consultar el área;
            # una petición por nombre exacto conserva su búsqueda SQL.
            exploracion_explicita = (
                hay_tema
                and es_peticion_exploratoria_explicita(pregunta)
                and not seguimiento_estructurado
            )
            consulta_combinada = (
                hay_tema
                and interpretacion.get("institucion") is not None
                and (interpretacion.get("programa") is None or exploracion_explicita)
                and not seguimiento_estructurado
            )
            explorar_tema = (
                False if seguimiento_estructurado
                else exploracion_explicita or consulta_combinada
                or es_exploracion_tematica(interpretacion)
            )

            # Solicitar aclaraciones cuando faltan datos identificables.
            # Las preguntas de intereses reconocidos se validan más abajo.
            if not explorar_tema and not seguimiento_estructurado:
                mensaje_aclaracion = validar_consulta(interpretacion)
                if mensaje_aclaracion is not None:
                    print("\n" + mensaje_aclaracion)
                    continue

            # Procesar consultas sobre intereses y areas academicas.
            if explorar_tema:

                institucion_pedida = interpretacion.get("institucion")
                modalidad_pedida = interpretacion.get("modalidad")
                cobertura = comprobar_cobertura(pregunta, indice_tematico)
                if cobertura["estado"] != "cobertura_directa":
                    contexto = crear_contexto()
                    if cobertura["estado"] == "sin_cobertura_directa":
                        temas = cobertura["temas_prioritarios"]
                        # En consultas combinadas se comprueban las alternativas
                        # dentro de la institución ANTES de ofrecerlas.
                        if institucion_pedida is not None:
                            todas_afines = buscar_afinidades(
                                temas, programas_semanticos,
                                limite=len(programas_semanticos)
                            )
                            afines = []
                            for candidato in todas_afines:
                                ofertas = buscar_programa(
                                    conexion, id_programa=candidato["id_programa"]
                                )
                                if filtrar_ofertas_combinadas(
                                    ofertas, institucion_pedida, modalidad_pedida
                                ):
                                    afines.append(candidato)
                                    if len(afines) == 5:
                                        break
                        else:
                            afines = buscar_afinidades(
                                temas, programas_semanticos, limite=5
                            )
                        opciones_pendientes = (
                            {"temas": temas, "candidatos": afines,
                             "institucion": institucion_pedida,
                             "modalidad": modalidad_pedida}
                            if afines else None
                        )
                        print("\n" + respuesta_sin_cobertura(
                            temas, bool(afines)
                        ))
                        if institucion_pedida is not None:
                            print(
                                "La búsqueda de alternativas se restringe a "
                                + institucion_pedida["nombre"] + "."
                            )
                    else:
                        opciones_pendientes = None
                        print("\n" + cobertura["mensaje"])
                    continue

                # Buscar dentro de los nombres respaldados por el tema,
                # no entre las 588 carreras indistintamente.
                indices_permitidos = [
                    i for i, (id_programa, _) in enumerate(programas_semanticos)
                    if id_programa in cobertura["ids_validos"]
                ]
                programas_permitidos = [
                    programas_semanticos[i] for i in indices_permitidos
                ]
                # Filtrar por institución antes de seleccionar el top 5:
                # hacerlo después podría descartar programas válidos de ella.
                if institucion_pedida is not None:
                    programas_permitidos = seleccionar_programas_de_institucion(
                        conexion, programas_permitidos,
                        institucion_pedida, modalidad_pedida
                    )
                    ids_permitidos = {pid for pid, _ in programas_permitidos}
                    indices_permitidos = [
                        i for i in indices_permitidos
                        if programas_semanticos[i][0] in ids_permitidos
                    ]
                if not programas_permitidos:
                    contexto = crear_contexto()
                    opciones_pendientes = None
                    print("\nNo encontré programas con cobertura temática directa "
                          "que cumplan los filtros de institución y modalidad "
                          "en el catálogo consultado.")
                    continue
                vectores_permitidos = vectores_semanticos[indices_permitidos]

                candidatos = buscar_semanticamente(
                    pregunta,
                    modelo_semantico,
                    programas_permitidos,
                    vectores_permitidos,
                    limite=5
                )

                resultados_semanticos = recuperar_ofertas(
                    conexion,
                    candidatos
                )

                # Si la pregunta también pidió una modalidad, aplicarla
                # a las ofertas de estos programas, no a todo el catálogo.
                if modalidad_pedida is not None or institucion_pedida is not None:
                    for resultado in resultados_semanticos:
                        resultado["ofertas"] = filtrar_ofertas_combinadas(
                            resultado["ofertas"], institucion_pedida, modalidad_pedida
                        )
                        resultado["total_ofertas"] = len(resultado["ofertas"])
                    resultados_semanticos = [
                        resultado for resultado in resultados_semanticos
                        if resultado["ofertas"]
                    ]

                print("\n" + respuesta_programas(
                    resultados_semanticos, cobertura["temas_prioritarios"]
                ))

                # Conservar los identificadores de los programas encontrados.
                contexto = crear_contexto()
                contexto["institucion"] = institucion_pedida
                contexto["modalidad"] = modalidad_pedida
                contexto["programas_semanticos"] = [
                    resultado["id_programa"]
                    for resultado in resultados_semanticos
                    if resultado["ofertas"]
                ]

                continue

            # Actualizar el contexto conversacional.
            nuevo_contexto = actualizar_contexto(
                contexto,
                interpretacion,
                conservar=seguimiento_academico,
            )

            if MODO_DIAGNOSTICO:
                mostrar_contexto(nuevo_contexto)

            institucion = nuevo_contexto["institucion"]
            programa = nuevo_contexto["programa"]
            modalidad = nuevo_contexto["modalidad"]

            # Buscar por programa, con filtros adicionales.
            if programa is not None:

                resultados = buscar_programa(
                    conexion,
                    id_programa=programa["id_programa"],
                    modalidad=modalidad
                )

                # Si se especifico una institucion, conservarla.
                if institucion is not None:
                    resultados = [
                        oferta for oferta in resultados
                        if oferta["institucion"] == institucion["nombre"]
                    ]

            # Buscar las ofertas de una institucion.
            elif institucion is not None:

                resultados = buscar_institucion(
                    conexion,
                    id_institucion=institucion["id_institucion"],
                    modalidad=modalidad
                )

            # Buscar todas las ofertas de una modalidad.
            elif modalidad is not None:

                resultados = filtrar_modalidad(
                    conexion,
                    modalidad=modalidad
                )

            else:
                print(
                    "\nNo se identificaron filtros suficientes "
                    "para realizar la busqueda."
                )
                continue

            # Guardar el contexto de la busqueda realizada.
            contexto = nuevo_contexto

            print("\n" + respuesta_ofertas(resultados, contexto))


if __name__ == "__main__":
    main()
