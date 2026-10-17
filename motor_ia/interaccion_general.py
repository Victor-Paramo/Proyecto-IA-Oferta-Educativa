"""Respuestas básicas y límites de alcance del asistente educativo.

Son reglas de interacción, no intenciones aprendidas ni nuevos modelos de IA.
Solo atienden expresiones generales claras; las consultas académicas se dejan
intactas para el clasificador, las entidades y la memoria conversacional.
"""

import re
import unicodedata


def normalizar_mensaje(mensaje):
    """Normalización local para no depender de PostgreSQL ni del modelo."""
    texto = unicodedata.normalize("NFD", mensaje.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", texto)).strip()


SALUDOS = {
    "hola", "hola buenos dias", "hola buenas tardes", "hola buenas noches",
    "buenas", "buenos dias", "buenas tardes", "buenas noches",
    "que tal", "hola que tal", "hey", "hola como estas",
}

AGRADECIMIENTOS = {
    "gracias", "muchas gracias", "muchas gracias me ayudaste",
    "gracias por tu ayuda", "te lo agradezco", "muy amable",
    "perfecto gracias", "excelente gracias", "gracias me ayudaste",
}

DESPEDIDAS = {
    "adios", "adios hablamos despues", "hasta luego", "hasta pronto",
    "nos vemos", "nos vemos luego", "hasta manana", "hasta la proxima",
    "me despido", "chao", "bye", "gracias adios",
}

AYUDA = {
    "ayuda", "que puedes hacer", "en que me puedes ayudar",
    "como me puedes ayudar", "que sabes hacer", "como funcionas",
    "que consultas puedo hacer", "para que sirves",
}

ORIENTACION = {
    "quiero orientacion vocacional", "necesito orientacion vocacional",
    "necesito orientacion", "quiero orientacion", "quisiera orientacion",
    "quiero ayuda para elegir una carrera",
    "no se que estudiar", "no se que licenciatura elegir",
}


_MENSAJE_FUENTE = (
    "Trabajo con un catálogo de licenciaturas de CDMX basado en registros "
    "SEP de abril de 2021; no compruebo la vigencia actual."
)


def detectar_interaccion_general(pregunta):
    """Devuelve {'mensaje': str, 'cerrar': bool}, o None.

    La comparación exacta de saludos y agradecimientos impide que un 'hola' al
    inicio de una búsqueda interrumpa la consulta académica.
    """
    texto = normalizar_mensaje(pregunta)
    if not texto:
        return None

    # Datos no incluidos en el catálogo. Prioritario incluso si se nombra
    # una carrera o institución: no fingir que PostgreSQL almacena precios.
    if (
        re.search(r"\b(colegiaturas?|mensualidades?|precios?|costos?|aranceles?)\b", texto)
        or re.search(r"\bcuanto (?:cuesta|cuestan|vale|valen|cobran)\b", texto)
        or re.search(r"\bcuanto se paga\b", texto)
        or re.search(r"\b(?:costo|precio) de (?:la |las |el |los )?(?:inscripcion|matricula)\b", texto)
    ):
        return {
            "mensaje": (
                "No tengo información de costos, colegiaturas o pagos en el "
                "catálogo SEP que consulto. No puedo dar una cantidad confiable. "
                "Para conocer precios actuales, consulta directamente con la "
                "institución. Sí puedo ayudarte a encontrar sus programas y modalidades."
            ),
            "cerrar": False,
        }

    if texto in DESPEDIDAS:
        return {
            "mensaje": "¡Hasta luego! Espero que la información te haya sido útil.",
            "cerrar": True,
        }

    if texto in AGRADECIMIENTOS:
        return {
            "mensaje": "¡Con gusto! Si necesitas consultar otra carrera o universidad, aquí estoy.",
            "cerrar": False,
        }

    if texto in SALUDOS:
        return {
            "mensaje": (
                "¡Hola! Puedo ayudarte a consultar carreras, universidades y "
                "modalidades. ¿Qué te gustaría estudiar?"
            ),
            "cerrar": False,
        }

    if texto in AYUDA:
        return {
            "mensaje": (
                "Puedo buscar carreras y universidades, filtrar modalidades y "
                "explorar programas relacionados con tus intereses. También "
                "puedes preguntarme por las opciones de una consulta anterior. "
                + _MENSAJE_FUENTE
            ),
            "cerrar": False,
        }

    # Orientación sin una carrera concreta. Reconocemos el ejemplo de las
    # pruebas y unas variantes generales, no peticiones académicas específicas.
    consulta_orientacion = (
        texto in ORIENTACION
        or re.fullmatch(
            r"(?:hola |buenas |buenos dias |buenas tardes )?"
            r"(?:quiero|quisiera|busco|necesito) "
            r"(?:orientacion|ayuda|asesoria) "
            r"(?:para |sobre |en )?"
            r"(?:elegir|escoger|seleccionar) "
            r"(?:una |mi )?(?:licenciatura|carrera)(?: universitaria)?",
            texto,
        ) is not None
    )
    if consulta_orientacion:
        return {
            "mensaje": (
                "Claro, puedo orientarte con las carreras registradas en el "
                "catálogo. Para empezar, ¿qué materias, actividades o temas "
                "te gustan? " + _MENSAJE_FUENTE
            ),
            "cerrar": False,
        }

    return None
