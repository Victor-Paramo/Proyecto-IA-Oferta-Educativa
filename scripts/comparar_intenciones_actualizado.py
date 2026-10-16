"""Compara el clasificador anterior con una ampliacion del entrenamiento.

No modifica PostgreSQL, MiniLM, app.py ni los archivos CSV.
Las 40 preguntas de diagnostico no se agregan al entrenamiento.
"""
import csv
import re
import unicodedata
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.metrics import accuracy_score, classification_report


RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^a-z0-9\\s]", " ", texto)
    return re.sub(r"\\s+", " ", texto).strip()


def leer_csv(ruta):
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    if not filas or not {"pregunta", "intencion"}.issubset(filas[0]):
        raise ValueError(f"CSV sin columnas pregunta e intencion: {ruta}")
    return [(fila["pregunta"], fila["intencion"].strip()) for fila in filas]


def construir_modelo(caracteres=False):
    if caracteres:
        tfidf = FeatureUnion([
            ("palabras", TfidfVectorizer(ngram_range=(1, 2))),
            ("caracteres", TfidfVectorizer(
                analyzer="char_wb", ngram_range=(3, 5)
            ))
        ])
    else:
        tfidf = TfidfVectorizer(ngram_range=(1, 2))

    return Pipeline([
        ("tfidf", tfidf),
        ("clasificador", LogisticRegression(max_iter=2000))
    ])


def ejecutar_comparacion(ruta_prueba, original, ampliado):
    prueba = leer_csv(ruta_prueba)
    print(f"\nPRUEBA: {ruta_prueba.name} ({len(prueba)} preguntas)")
    for nombre, entrenamiento, caracteres in (
        ("Original: 80 + palabras", original, False),
        ("Ampliado: 136 + palabras", ampliado, False),
        ("Ampliado: 136 + palabras y caracteres", ampliado, True)
    ):
        comunes = {normalizar(q) for q, _ in prueba} & {
            normalizar(q) for q, _ in entrenamiento
        }
        if comunes:
            print(f"  ATENCION: {len(comunes)} preguntas repetidas entre entrenamiento y prueba.")
            print("  No se puede considerar una evaluacion independiente.")
            continue

        modelo = construir_modelo(caracteres)
        modelo.fit(
            [normalizar(q) for q, _ in entrenamiento],
            [y for _, y in entrenamiento]
        )
        reales = [y for _, y in prueba]
        predichas = modelo.predict([normalizar(q) for q, _ in prueba])
        aciertos = sum(a == b for a, b in zip(reales, predichas))
        print(f"\n  {nombre}: {aciertos}/{len(prueba)} = "
              f"{accuracy_score(reales, predichas):.2%}")
        for (pregunta, real), predicha in zip(prueba, predichas):
            if real != predicha:
                print(f"    ERROR | real={real} | predicha={predicha} | {pregunta}")

    print("\n  Nota: con pocas preguntas la diferencia puede deberse al azar.")


def main():
    original = leer_csv(DATOS / "intenciones_entrenamiento_original_80.csv")
    ampliado = leer_csv(DATOS / "intenciones_entrenamiento.csv")

    print("=" * 64)
    print("COMPARACION DEL CLASIFICADOR DE INTENCIONES")
    print("=" * 64)
    print(f"Ejemplos originales: {len(original)}")
    print(f"Ejemplos ampliados: {len(ampliado)}")
    print("Modelo: regresion logistica, sin nuevos modelos preentrenados.")

    ejecutar_comparacion(
        DATOS / "pruebas_intenciones_nuevas.csv", original, ampliado
    )

    # Si ya existe el conjunto independiente anterior de 24 preguntas,
    # tambien se evalua, sin mezclarlo con el entrenamiento.
    ruta_anterior = DATOS / "intenciones_evaluacion.csv"
    if ruta_anterior.is_file():
        ejecutar_comparacion(ruta_anterior, original, ampliado)
    else:
        print("\nNo se encontro intenciones_evaluacion.csv. "
              "Se omitio esa comparacion opcional.")

    pregunta = "Quiero pronosticar huracanes"
    print(f"\nCASO OBJETIVO: {pregunta}")
    for nombre, entrenamiento, caracteres in (
        ("Anterior", original, False),
        ("Actualizado", ampliado, True)
    ):
        modelo = construir_modelo(caracteres)
        modelo.fit(
            [normalizar(q) for q, _ in entrenamiento],
            [y for _, y in entrenamiento]
        )
        pred = modelo.predict([normalizar(pregunta)])[0]
        confianza = modelo.predict_proba([normalizar(pregunta)]).max()
        print(f"  {nombre}: {pred} (puntuacion {confianza:.2%})")
    print("\nIMPORTANTE: Esta prueba no modifica los archivos ni los pesos MiniLM.")


if __name__ == "__main__":
    main()
