
from motor_ia.entidades import normalizar_texto


# Crear una memoria vacia para la conversacion.
def crear_contexto():
    return {
        "institucion": None,
        "programa": None,
        "modalidad": None,
        "programas_semanticos": []
    }


# Comprobar si una pregunta hace referencia a la consulta anterior.
def es_seguimiento(pregunta):
    texto = normalizar_texto(pregunta)

    expresiones = [
        "y cuales",
        "y cuales de esas",
        "de esas",
        "de esos",
        "de las anteriores",
        "de los anteriores",
        "de esas opciones",
        "de esos resultados",
        "de esa lista",
        "de esas carreras",
        "de las opciones anteriores",
        "ahora solo",
        "y las",
        "y los"
    ]

    return any(
        texto.startswith(expresion)
        for expresion in expresiones
    )


# Actualizar los filtros de la conversacion.
def actualizar_contexto(contexto, interpretacion):
    pregunta = interpretacion["pregunta"]
    institucion = interpretacion["institucion"]
    programa = interpretacion["programa"]
    modalidad = interpretacion["modalidad"]

    # Los seguimientos conservan los filtros anteriores.
    if es_seguimiento(pregunta):
        nuevo = contexto.copy()
    else:
        # Una nueva consulta comienza con filtros vacios.
        nuevo = crear_contexto()

    # Incorporar las entidades encontradas.
    if institucion is not None:
        nuevo["institucion"] = institucion

    if programa is not None:
        nuevo["programa"] = programa

    if modalidad is not None:
        nuevo["modalidad"] = modalidad

    return nuevo


# Mostrar el contexto actual.
def mostrar_contexto(contexto):
    institucion = contexto["institucion"]
    programa = contexto["programa"]

    print("\nCONTEXTO ACTUAL:")
    print(
        "Institucion:",
        institucion["nombre"] if institucion else "No especificada"
    )
    print(
        "Programa:",
        programa["nombre"] if programa else "No especificado"
    )
    print(
        "Modalidad:",
        contexto["modalidad"] or "No especificada"
    )
    if contexto["programas_semanticos"]:
        print("Programas semanticos guardados:", len(contexto["programas_semanticos"]))
