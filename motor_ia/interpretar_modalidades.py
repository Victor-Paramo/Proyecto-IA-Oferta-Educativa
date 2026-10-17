"""Interpretación explícita de modalidades, sin modificar los modelos de IA.

Distingue modalidades solicitadas de modalidades expresamente descartadas.
El catálogo define las tres modalidades: ESCOLARIZADA, MIXTA y NO ESCOLARIZADA.
"""

import re
import unicodedata


MODALIDADES = ("ESCOLARIZADA", "MIXTA", "NO ESCOLARIZADA")


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", texto)).strip()


# Importante: NO ESCOLARIZADA tiene prioridad sobre ESCOLARIZADA.
EXPRESIONES = {
    "NO ESCOLARIZADA": (
        r"\bno escolarizad[oa]s?\b",
        r"\ba distancia\b", r"\ben linea\b", r"\bonline\b",
        r"\bvirtual(?:es)?\b", r"\bremot[oa]s?\b",
        r"\bdesde (?:mi |la )?casa\b", r"\bpor internet\b",
        r"\bsin (?:tener que )?(?:ir|asistir) (?:a clases|al campus|a la universidad)\b",
    ),
    "MIXTA": (
        r"\bmixt[oa]s?\b", r"\bsemipresencial(?:es)?\b",
        r"\bsemi presencial(?:es)?\b", r"\bhibrid[oa]s?\b",
        r"\bsemiescolarizad[oa]s?\b",
    ),
    "ESCOLARIZADA": (
        r"\bescolarizad[oa]s?\b", r"\bpresencial(?:es)?\b",
        r"\ben persona\b", r"\ben el salon de clases\b",
        r"\bclases en (?:el )?salon\b",
    ),
}

PATRONES = {
    modalidad: tuple(re.compile(patron) for patron in patrones)
    for modalidad, patrones in EXPRESIONES.items()
}

# Se busca una negación unida al tipo de modalidad; no basta con que
# la palabra "no" aparezca en cualquier parte de la pregunta.
NEGACION_PREVIA = re.compile(
    r"(?:"
    r"no\s+(?:quiero|deseo|busco|prefiero|necesito|me\s+interesa|me\s+gustaria)"
    r"(?:\s+(?:cursar|estudiar|ver|tomar|elegir))?"
    r"|que\s+no\s+(?:sea|sean)"
    r"|sin|excepto|excluir|excluye|descartar|descarta|evitar|evita"
    r")\s+"
    r"(?:(?:ninguna?|nada|la|las|los|el|una?|de|en|que|modalidad|modalidades|"
    r"opciones|opcion|carreras|carrera|estudios|cursos|clases)\s+){0,5}$"
)


def analizar_modalidades(pregunta):
    """Devuelve modalidad solicitada, descartadas y estado de ambigüedad.

    No ejecuta SQL ni clasifica intenciones; solo interpreta expresiones
    explícitas. Si hay dos modalidades positivas diferentes, pide aclaración.
    """
    texto = normalizar(pregunta)
    coincidencias = []
    for modalidad, patrones in PATRONES.items():
        for patron in patrones:
            for match in patron.finditer(texto):
                coincidencias.append((match.start(), match.end(), modalidad))

    # Una sola coincidencia por tramo, priorizando la expresión completa
    # "no escolarizada" frente a la subcadena "escolarizada".
    coincidencias.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    spans = []
    for inicio, fin, modalidad in coincidencias:
        if not any(inicio < prev_fin and fin > prev_ini for prev_ini, prev_fin, _ in spans):
            spans.append((inicio, fin, modalidad))
    spans.sort()

    solicitadas = []
    excluidas = []
    for inicio, _, modalidad in spans:
        previo = texto[max(0, inicio - 115):inicio]
        destino = excluidas if NEGACION_PREVIA.search(previo) else solicitadas
        if modalidad not in destino:
            destino.append(modalidad)

    # La expresión contradictoria requiere aclaración; no escoger al azar.
    contradictorias = set(solicitadas) & set(excluidas)
    candidatas = [m for m in solicitadas if m not in excluidas]
    ambigua = len(candidatas) > 1 or bool(contradictorias)
    return {
        "modalidad": candidatas[-1] if len(candidatas) == 1 and not ambigua else None,
        "solicitadas": tuple(solicitadas),
        "excluidas": tuple(excluidas),
        "ambigua": ambigua,
    }


def mensaje_aclaracion_modalidad(analisis):
    if analisis["ambigua"]:
        return ("Mencionaste más de una modalidad o instrucciones contradictorias. "
                "¿Quieres escolarizada, mixta o no escolarizada?")
    if analisis["excluidas"] and analisis["modalidad"] is None:
        alternativas = [m.lower() for m in MODALIDADES if m not in analisis["excluidas"]]
        return ("Entendí que no quieres la modalidad "
                + ", ".join(m.lower() for m in analisis["excluidas"])
                + ". ¿Prefieres " + " o ".join(alternativas) + "?")
    return None


def ajustar_interpretacion(interpretacion, analisis, tiene_tema=False):
    """Aplica el filtro explícito al dict de interpretación, sin perder entidades."""
    if analisis["modalidad"] is None:
        return interpretacion

    interpretacion = interpretacion.copy()
    interpretacion["modalidad"] = analisis["modalidad"]
    if interpretacion.get("programa") is None and interpretacion.get("institucion") is None:
        interpretacion["intencion"] = "explorar_area" if tiene_tema else "filtrar_modalidad"
    return interpretacion
