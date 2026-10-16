"""Experimento de verificacion semantica usando el MISMO modelo MiniLM.

Esta version NO decide automaticamente si una carrera es valida.
Entrega puntuaciones comparables para evaluar criterios de rechazo antes de
integrarlos a app.py. No lee las etiquetas 0/1/2 durante la ejecucion normal.
"""
import re
import unicodedata

from sentence_transformers import util


# Palabras de conversacion; NO son nombres de areas academicas o carreras.
# No se intenta cubrir toda la gramatica del espanol.
PALABRAS_DE_APOYO = {
    "a", "al", "algo", "con", "cual", "cuales", "de", "del", "donde",
    "el", "en", "entre", "es", "estudiar", "estudio", "hacer", "interesa",
    "interesaria", "interesan", "la", "las", "lo", "los", "me", "mi", "mis",
    "mucho", "para", "podria", "podrias", "por", "que", "quiero", "quisiera",
    "ser", "sobre", "te", "tener", "un", "una", "unos", "unas", "y",
    "gustaria", "gusta", "gustan", "carrera", "carreras", "licenciatura",
    "licenciaturas", "universidad", "universidades", "opciones",
}


def normalizar_palabras(texto):
    """Devuelve una lista de palabras en minusculas y sin tildes."""
    normalizado = "".join(
        caracter for caracter in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(caracter) != "Mn"
    )
    return re.findall(r"[a-z0-9]+", normalizado)


def extraer_tema(pregunta):
    """Elimina palabras conversacionales, conservando terminos del interes.

    Es una heuristica simple. Si no encuentra terminos, conserva la frase
    original para evitar enviar una cadena vacia a MiniLM.
    """
    palabras = normalizar_palabras(pregunta)
    relevantes = [
        palabra for palabra in palabras
        if palabra not in PALABRAS_DE_APOYO and len(palabra) > 2
    ]
    return " ".join(relevantes) if relevantes else pregunta.strip()


def comparar_enfoques(pregunta, candidatos, modelo):
    """Anexa similitud focal y puntuacion conservadora a candidatos MiniLM.

    candidatos: lista de dicts con 'nombre' (o 'programa') y 'similitud'.
    No inventa carreras, no aplica un umbral, y no modifica los dicts originales.
    """
    if not candidatos:
        return []

    tema = extraer_tema(pregunta)
    nombres = [c.get("nombre", c.get("programa")) for c in candidatos]
    if any(not nombre for nombre in nombres):
        raise ValueError("Cada candidato necesita 'nombre' o 'programa'.")

    # Un solo modelo MiniLM; codificamos en lote para evitar trabajo repetido.
    vectores = modelo.encode(
        [tema] + nombres,
        convert_to_tensor=True,
        show_progress_bar=False,
    )
    similitudes = util.cos_sim(vectores[:1], vectores[1:])[0]

    salida = []
    for candidato, similitud_focal in zip(candidatos, similitudes):
        resultado = dict(candidato)
        puntuacion_original = float(candidato["similitud"])
        puntuacion_focal = float(similitud_focal)
        resultado["tema_extraido"] = tema
        resultado["similitud_focal"] = puntuacion_focal
        resultado["puntuacion_conservadora"] = min(
            puntuacion_original, puntuacion_focal
        )
        salida.append(resultado)
    return salida


def aplicar_umbral(candidatos_evaluados, umbral, campo="puntuacion_conservadora"):
    """Filtra usando un umbral EXPLICITO calibrado externamente.

    No tiene un umbral fijo de fabrica: este debe verificarse previamente con
    datos independientes. Durante el diagnostico, NO usar en app.py.
    """
    if not 0 <= umbral <= 1:
        raise ValueError("El umbral debe estar entre 0 y 1.")
    if campo not in {"similitud", "similitud_focal", "puntuacion_conservadora"}:
        raise ValueError("Campo de puntuacion no reconocido.")
    return [fila for fila in candidatos_evaluados if fila[campo] >= umbral]
