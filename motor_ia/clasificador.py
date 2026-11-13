
import csv
import re
import unicodedata
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline, FeatureUnion


# Localizar el archivo de entrenamiento.
RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO_CSV = RAIZ / "datos" / "intenciones_entrenamiento.csv"


# Normalizar las preguntas.
def normalizar_texto(texto):
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        caracter for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


# Cargar las preguntas y sus intenciones.
def cargar_datos():
    preguntas = []
    intenciones = []

    with open(ARCHIVO_CSV, "r", encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)

        for fila in lector:
            preguntas.append(normalizar_texto(fila["pregunta"]))
            intenciones.append(fila["intencion"].strip())

    return preguntas, intenciones


# Entrenar y evaluar el clasificador.
def entrenar_modelo():
    preguntas, intenciones = cargar_datos()

    X_entrenamiento, X_prueba, y_entrenamiento, y_prueba = train_test_split(
        preguntas,
        intenciones,
        test_size=0.25,
        random_state=42,
        stratify=intenciones
    )

    # TF-IDF de palabras y caracteres con la misma regresion logistica.
    modelo = Pipeline([
        ("tfidf", FeatureUnion([
            ("palabras", TfidfVectorizer(ngram_range=(1, 2))),
            ("caracteres", TfidfVectorizer(
                analyzer="char_wb", ngram_range=(3, 5)
            ))
        ])),
        ("clasificador", LogisticRegression(max_iter=2000))
    ])

    modelo.fit(X_entrenamiento, y_entrenamiento)

    predicciones = modelo.predict(X_prueba)
    print("\nResultados individuales de las pruebas:")

    for pregunta, real, predicha in zip(
        X_prueba, y_prueba, predicciones
    ):
        estado = "CORRECTO" if real == predicha else "ERROR"

        print(f"\nPregunta: {pregunta}")
        print(f"Intencion real: {real}")
        print(f"Intencion predicha: {predicha}")
        print(f"Resultado: {estado}")
    exactitud = accuracy_score(y_prueba, predicciones)

    print(f"Preguntas de entrenamiento: {len(X_entrenamiento)}")
    print(f"Preguntas de prueba: {len(X_prueba)}")
    print(f"Exactitud inicial: {exactitud:.2%}")

    print("\nReporte de clasificacion:")
    print(classification_report(
        y_prueba,
        predicciones,
        zero_division=0
    ))

    return modelo


# Probar nuevas preguntas.
def probar_modelo(modelo):
    while True:
        pregunta = input("\nEscribe tu pregunta (o 'salir'): ").strip()

        if normalizar_texto(pregunta) == "salir":
            break

        if not pregunta:
            continue

        pregunta_normalizada = normalizar_texto(pregunta)

        intencion = modelo.predict([pregunta_normalizada])[0]
        probabilidades = modelo.predict_proba([pregunta_normalizada])[0]

        confianza = max(probabilidades)

        print("Intencion detectada:", intencion)
        print(f"Probabilidad estimada: {confianza:.2%}")


def main():
    print("=" * 55)
    print("OFERTA EDUCATIVA CIUDAD DE MEXICO 2.0")
    print("Modulo 2: Clasificador de intenciones")
    print("=" * 55)

    modelo = entrenar_modelo()
    probar_modelo(modelo)


if __name__ == "__main__":
    main()
