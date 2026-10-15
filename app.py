
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
    es_seguimiento
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

        print("Motor semantico preparado.")

        # Crear una memoria para la sesion actual.
        contexto = crear_contexto()

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

            # Interpretar la pregunta utilizando el motor de IA.
            interpretacion = interpretar_pregunta(
                pregunta,
                modelo,
                instituciones,
                programas
            )

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
                mostrar_contexto(contexto)
                print(f"\nOfertas encontradas: {len(resultados)}")
                for oferta in resultados[:15]:
                    print(
                        f"- {oferta['institucion']} | "
                        f"{oferta['programa']} | "
                        f"{oferta['plantel'] or 'Plantel no especificado'} | "
                        f"{oferta['modalidad']}"
                    )
                if len(resultados) > 15:
                    print(f"\nMostrando 15 de {len(resultados)} ofertas.")
                continue

            # Procesar consultas sobre intereses y areas academicas.
            if interpretacion["intencion"] == "explorar_area":

                candidatos = buscar_semanticamente(
                    pregunta,
                    modelo_semantico,
                    programas_semanticos,
                    vectores_semanticos,
                    limite=5
                )

                resultados_semanticos = recuperar_ofertas(
                    conexion,
                    candidatos
                )

                print("\nPROGRAMAS RELACIONADOS:")

                for posicion, resultado in enumerate(
                    resultados_semanticos, start=1
                ):
                    print(
                        f"\n{posicion}. {resultado['programa']}"
                    )
                    print(
                        f"Similitud: {resultado['similitud']:.4f}"
                    )
                    print(
                        f"Ofertas registradas: "
                        f"{resultado['total_ofertas']}"
                    )

                    for oferta in resultado["ofertas"][:3]:
                        print(
                            f"  - {oferta['institucion']} | "
                            f"{oferta['plantel'] or 'No especificado'} | "
                            f"{oferta['modalidad']}"
                        )

                # Conservar los identificadores de los programas encontrados.
                contexto = crear_contexto()
                contexto["programas_semanticos"] = [
                    resultado["id_programa"]
                    for resultado in resultados_semanticos
                    if resultado["total_ofertas"] > 0
                ]

                continue

            # Actualizar el contexto conversacional.
            nuevo_contexto = actualizar_contexto(
                contexto,
                interpretacion
            )

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

            print(f"\nOfertas encontradas: {len(resultados)}")

            for oferta in resultados[:15]:
                print(
                    f"- {oferta['institucion']} | "
                    f"{oferta['programa']} | "
                    f"{oferta['plantel'] or 'Plantel no especificado'} | "
                    f"{oferta['modalidad']}"
                )

            if len(resultados) > 15:
                print(
                    f"\nMostrando 15 de {len(resultados)} ofertas."
                )


if __name__ == "__main__":
    main()
