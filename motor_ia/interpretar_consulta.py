
import csv
import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from entidades import (
    conectar_bd,
    normalizar_texto,
    cargar_instituciones,
    cargar_programas,
    extraer_institucion,
    extraer_programa,
    extraer_modalidad
)


# Localizar los datos de entrenamiento.
RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO_CSV = RAIZ / "datos" / "intenciones_entrenamiento.csv"


# Cargar las preguntas e intenciones.
def cargar_entrenamiento():
    preguntas = []
    intenciones = []

    with open(ARCHIVO_CSV, "r", encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)

        for fila in lector:
            preguntas.append(normalizar_texto(fila["pregunta"]))
            intenciones.append(fila["intencion"].strip())

    return preguntas, intenciones


# Entrenar el clasificador de intenciones.
def preparar_clasificador():
    preguntas, intenciones = cargar_entrenamiento()

    modelo = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
        ("clasificador", LogisticRegression(max_iter=1000))
    ])

    modelo.fit(preguntas, intenciones)

    print(f"Clasificador entrenado con {len(preguntas)} preguntas.")

    return modelo


# Interpretar una pregunta usando IA y entidades.
def interpretar_pregunta(pregunta, modelo, instituciones, programas):
    texto = normalizar_texto(pregunta)

    # Identificar la intencion.
    intencion = modelo.predict([texto])[0]

    probabilidades = modelo.predict_proba([texto])[0]
    confianza = float(max(probabilidades))

    # Identificar las entidades.
    institucion = extraer_institucion(pregunta, instituciones)
    programa = extraer_programa(pregunta, programas)
    modalidad = extraer_modalidad(pregunta)

    resultado = {
        "pregunta": pregunta,
        "intencion": intencion,
        "confianza": round(confianza, 4),
        "institucion": institucion,
        "programa": programa,
        "modalidad": modalidad
    }

    return resultado


# Programa principal.
def main():
    print("=" * 60)
    print("OFERTA EDUCATIVA CIUDAD DE MEXICO 2.0")
    print("Modulo 4: Interpretacion de consultas")
    print("=" * 60)

    # Entrenar el modelo una sola vez.
    modelo = preparar_clasificador()

    # Conectar a PostgreSQL y cargar los catalogos.
    with conectar_bd() as conexion:
        instituciones = cargar_instituciones(conexion)
        programas = cargar_programas(conexion)

        print("\nConexion establecida con PostgreSQL.")
        print(f"Instituciones cargadas: {len(instituciones)}")
        print(f"Programas cargados: {len(programas)}")

        while True:
            pregunta = input(
                "\nEscribe tu pregunta (o 'salir'): "
            ).strip()

            if normalizar_texto(pregunta) == "salir":
                print("Programa finalizado.")
                break

            if not pregunta:
                print("Debes escribir una pregunta.")
                continue

            resultado = interpretar_pregunta(
                pregunta,
                modelo,
                instituciones,
                programas
            )

            print("\nINTERPRETACION:")
            print(json.dumps(
                resultado,
                indent=4,
                ensure_ascii=False
            ))


if __name__ == "__main__":
    main()
