
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
                        if ofertas:
                            resultados_afines.append({**candidato, "ofertas": ofertas})
                    contexto = crear_contexto()
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
            # Conservar los programas semanticos en preguntas de seguimiento.
            if es_seguimiento(pregunta) and contexto["programas_semanticos"]:
                nuevo_contexto = actualizar_contexto(contexto, interpretacion)
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
            )

            # Distinguir búsquedas por intereses de filtros de modalidad.
            # Si hay un seguimiento estructurado, conservamos la consulta
            # anterior en lugar de reencaminarla a MiniLM.
            explorar_tema = (
                False if seguimiento_estructurado
                else es_exploracion_tematica(interpretacion)
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

                cobertura = comprobar_cobertura(pregunta, indice_tematico)
                if cobertura["estado"] != "cobertura_directa":
                    contexto = crear_contexto()
                    if cobertura["estado"] == "sin_cobertura_directa":
                        temas = cobertura["temas_prioritarios"]
                        afines = buscar_afinidades(
                            temas, programas_semanticos, limite=5
                        )
                        opciones_pendientes = (
                            {"temas": temas, "candidatos": afines}
                            if afines else None
                        )
                        print("\n" + respuesta_sin_cobertura(
                            temas, bool(afines)
                        ))
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
                modalidad_pedida = interpretacion.get("modalidad")
                if modalidad_pedida is not None:
                    for resultado in resultados_semanticos:
                        resultado["ofertas"] = [
                            oferta for oferta in resultado["ofertas"]
                            if oferta["modalidad"] == modalidad_pedida
                        ]
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
                interpretacion
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
