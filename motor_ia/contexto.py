
import re

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
    texto = normalizar_texto(pregunta).lstrip("¿¡?!.,:; ")

    # Un cambio de tema explícito debe iniciar un contexto nuevo aunque
    # mencione la universidad anterior ("dejemos esa universidad").
    if texto.startswith((
        "dejemos", "olvidemos", "cambiemos", "cambiando de tema"
    )):
        return False

    # "Y si prefiero una modalidad mixta" conserva el ámbito anterior.
    # Exigimos una modalidad explícita para no heredar instituciones cuando
    # el estudiante cambia de carrera ("Y si prefiero Psicología").
    if re.match(r"^(?:y\s+)?si\s+(?:prefiero|quiero|quisiera|elijo|cambio)\b", texto):
        if re.search(
            r"\b(?:modalidad(?:es)?|mixt[oa]s?|semipresencial(?:es)?|"
            r"escolarizad[oa]s?|presencial(?:es)?|a distancia|"
            r"en linea|desde casa)\b",
            texto,
        ):
            return True

    # Las referencias a resultados anteriores pueden aparecer en cualquier
    # parte de la pregunta, no necesariamente al principio.
    referencias = (
        "esa licenciatura", "esta licenciatura", "esa carrera", "esta carrera",
        "ese programa", "este programa", "esa institucion", "esta institucion",
        "esa universidad", "esta universidad", "ese instituto", "este instituto",
        "dicha institucion", "dicha universidad", "esas opciones", "esos resultados",
        "esas carreras", "esos programas", "las opciones anteriores",
        "las anteriores", "los anteriores", "de esa lista", "de esas",
        "sus planteles", "sus campus",
        "de esos", "de las anteriores", "de los anteriores",
    )
    if any(referencia in texto for referencia in referencias):
        return True

    # Seguimientos cortos que mantienen el tema de la conversacion.
    inicios = (
        "y cuales", "y las", "y los", "ahora solo",
        "solo las", "solo los", "y que opciones",
        "y hay alguna", "y hay algunas", "que opciones hay en modalidad",
    )
    if texto.startswith(inicios):
        return True

    # 'Ahora muestrame las opciones mixtas' es un seguimiento, pero
    # 'Ahora muestrame las carreras de Arquitectura' puede ser un tema nuevo.
    comienzos = (
        "ahora muestrame", "muestrame", "ahora quiero ver",
        "ahora dime", "puedes mostrarme",
    )
    marcadores = (
        "las opciones", "los resultados", "las anteriores",
        "los anteriores", "esas", "esos", "de antes",
    )
    return texto.startswith(comienzos) and any(
        marcador in texto for marcador in marcadores
    )


def es_seguimiento_estructurado(pregunta, contexto):
    """Permite reutilizar la ultima carrera o universidad, sin confundirla
    con una lista de programas recomendados por MiniLM."""
    return (
        es_seguimiento(pregunta)
        and not contexto["programas_semanticos"]
        and (contexto["institucion"] is not None or contexto["programa"] is not None)
    )


# Actualizar los filtros de la conversacion.
def actualizar_contexto(contexto, interpretacion, conservar=None):
    pregunta = interpretacion["pregunta"]
    institucion = interpretacion["institucion"]
    programa = interpretacion["programa"]
    modalidad = interpretacion["modalidad"]

    # La decisión de continuidad del orquestador tiene prioridad sobre
    # las pistas literales; ambas deben producir el mismo contexto.
    if conservar is None:
        conservar = es_seguimiento(pregunta)
    if conservar:
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
