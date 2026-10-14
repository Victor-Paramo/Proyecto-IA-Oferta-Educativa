
import csv
import re
import unicodedata
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix


# Rutas de los archivos.
RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO_ENTRENAMIENTO = RAIZ / "datos" / "intenciones_entrenamiento.csv"
ARCHIVO_EVALUACION = RAIZ / "datos" / "intenciones_evaluacion.csv"


# Normalizar el texto.
def normalizar_texto(texto):
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        caracter for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


# Leer preguntas e intenciones de un archivo CSV.
def cargar_datos(ruta):
    preguntas = []
    intenciones = []

    with open(ruta, "r", encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)

        for fila in lector:
            preguntas.append(normalizar_texto(fila["pregunta"]))
            intenciones.append(fila["intencion"].strip())

    return preguntas, intenciones


# Definir los algoritmos.
def crear_modelos():
    return {
        "Regresion logistica": LogisticRegression(max_iter=1000),
        "Naive Bayes": MultinomialNB(),
        "SVM lineal": LinearSVC()
    }


# Crear un pipeline independiente para cada algoritmo.
def crear_pipeline(algoritmo):
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
        ("clasificador", algoritmo)
    ])


# Comparar modelos.
def comparar_modelos():
    X_entrenamiento, y_entrenamiento = cargar_datos(
        ARCHIVO_ENTRENAMIENTO
    )

    X_evaluacion, y_evaluacion = cargar_datos(
        ARCHIVO_EVALUACION
    )

    # Comprobar que ninguna pregunta aparece en ambos archivos.
    repetidas = set(X_entrenamiento) & set(X_evaluacion)

    if repetidas:
        print("ERROR: existen preguntas repetidas entre los archivos.")
        for pregunta in sorted(repetidas):
            print(pregunta)
        return

    print("=" * 65)
    print("OFERTA EDUCATIVA CIUDAD DE MEXICO 2.0")
    print("Evaluacion independiente de algoritmos")
    print("=" * 65)

    print(f"\nPreguntas de entrenamiento: {len(X_entrenamiento)}")
    print(f"Preguntas independientes: {len(X_evaluacion)}")

    resultados = []

    # Primero: validacion cruzada dentro del entrenamiento.
    validacion = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42
    )

    for nombre, algoritmo in crear_modelos().items():
        modelo = crear_pipeline(algoritmo)

        metricas = cross_validate(
            modelo,
            X_entrenamiento,
            y_entrenamiento,
            cv=validacion,
            scoring=["accuracy", "f1_macro"]
        )

        exactitud_cv = metricas["test_accuracy"].mean()
        f1_cv = metricas["test_f1_macro"].mean()

        # Entrenar con las 80 preguntas.
        modelo.fit(X_entrenamiento, y_entrenamiento)

        # Evaluar con las 24 preguntas independientes.
        predicciones = modelo.predict(X_evaluacion)

        exactitud = accuracy_score(y_evaluacion, predicciones)
        f1 = f1_score(y_evaluacion, predicciones, average="macro")

        resultados.append(
            (nombre, exactitud_cv, f1_cv, exactitud, f1)
        )

        print("\n" + "-" * 65)
        print(f"ALGORITMO: {nombre}")
        print("-" * 65)

        print(f"Exactitud validacion cruzada: {exactitud_cv:.2%}")
        print(f"F1 validacion cruzada: {f1_cv:.2%}")
        print(f"Exactitud independiente: {exactitud:.2%}")
        print(f"F1 independiente: {f1:.2%}")

        print("\nReporte de clasificacion:")
        print(classification_report(
            y_evaluacion,
            predicciones,
            zero_division=0
        ))

        print("Matriz de confusion:")
        clases = sorted(set(y_entrenamiento) | set(y_evaluacion))

        print("Orden de clases:", clases)
        print(confusion_matrix(
            y_evaluacion,
            predicciones,
            labels=clases
        ))

        print("\nPredicciones incorrectas:")

        errores = 0

        for pregunta, real, predicha in zip(
            X_evaluacion, y_evaluacion, predicciones
        ):
            if real != predicha:
                errores += 1
                print(f"Pregunta: {pregunta}")
                print(f"Esperada: {real}")
                print(f"Predicha: {predicha}\n")

        if errores == 0:
            print("Ninguna.")

    print("\n" + "=" * 65)
    print("RESUMEN FINAL")
    print("=" * 65)

    print(
        f"{'Algoritmo':22} {'CV':>9} "
        f"{'F1 CV':>9} {'Prueba':>9} {'F1':>9}"
    )

    for nombre, cv, f1_cv, exactitud, f1 in resultados:
        print(
            f"{nombre:22} {cv:>8.2%} "
            f"{f1_cv:>8.2%} {exactitud:>8.2%} "
            f"{f1:>8.2%}"
        )


if __name__ == "__main__":
    comparar_modelos()
