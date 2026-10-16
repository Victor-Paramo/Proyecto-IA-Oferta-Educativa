"""Diagnostico de rechazo semantico SIN modificar app.py ni PostgreSQL.

Compara 3 puntuaciones usando las mismas 60 parejas pregunta-programa:
  1) MiniLM original; 2) MiniLM con tema extraido; 3) minimo de ambas.
Evalua umbrales por validacion dejando fuera UNA PREGUNTA COMPLETA a la vez.
Las etiquetas 0/1/2 solo se leen para medir el experimento.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sklearn.metrics import fbeta_score, precision_score, recall_score

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from motor_ia.validacion_semantica import comparar_enfoques, extraer_tema

RUTA_MODELO = RAIZ / "modelos_ia" / "minilm"
RUTA_CSV = RAIZ / "datos" / "evaluacion_semantica_escala_0_2.csv"
SALIDA = RAIZ / "datos" / "diagnostico_validacion_semantica.csv"

CAMPOS = ("similitud", "similitud_focal", "puntuacion_conservadora")


def leer_archivo():
    if not RUTA_CSV.is_file():
        raise SystemExit(f"No existe el CSV: {RUTA_CSV}")
    with RUTA_CSV.open(encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    if not filas:
        raise SystemExit("El CSV esta vacio.")
    columnas = {"caso", "pregunta", "programa", "similitud", "pertinencia_0_2"}
    if not columnas.issubset(filas[0]):
        raise SystemExit(f"El CSV no incluye columnas: {columnas-set(filas[0])}")
    for fila in filas:
        if fila["pertinencia_0_2"] not in {"0", "1", "2"}:
            raise SystemExit("Hay etiquetas incompletas o incorrectas.")
    return filas


def mejor_umbral(filas_entrenamiento, campo):
    """Selecciona un umbral priorizando precision (F0.5), sin ver el test.

    El conjunto de entrenamiento contiene PREGUNTAS completas diferentes
    de la pregunta a evaluar. Los empates prefieren un umbral mas estricto.
    """
    verdaderos = [int(f["pertinencia_0_2"]) >= 1 for f in filas_entrenamiento]
    valores = sorted(set(float(f[campo]) for f in filas_entrenamiento))
    # Puntos medios y extremos para considerar aceptar/rechazar todos.
    umbrales = [0.0] + [(a+b)/2 for a,b in zip(valores, valores[1:])] + [1.0]
    mejor = None
    for umbral in umbrales:
        predicciones = [float(f[campo]) >= umbral for f in filas_entrenamiento]
        metrica = fbeta_score(verdaderos, predicciones, beta=0.5, zero_division=0)
        # Desempate: mayor precision, menor cantidad de falsos positivos.
        precision = precision_score(verdaderos, predicciones, zero_division=0)
        criterio = (metrica, precision, umbral)
        if mejor is None or criterio > mejor[0]:
            mejor = (criterio, umbral)
    return mejor[1]


def validar_dejando_fuera_preguntas(filas, campo):
    casos = sorted(set(f["caso"] for f in filas))
    resultados = []
    for caso in casos:
        entrenamiento = [f for f in filas if f["caso"] != caso]
        prueba = [f for f in filas if f["caso"] == caso]
        umbral = mejor_umbral(entrenamiento, campo)
        for fila in prueba:
            predicho = int(float(fila[campo]) >= umbral)
            correcto = int(int(fila["pertinencia_0_2"]) >= 1)
            resultados.append((caso, fila, umbral, predicho, correcto))
    return resultados


def mostrar_resultados(resultados, campo):
    y = [r[4] for r in resultados]
    p = [r[3] for r in resultados]
    precision = precision_score(y, p, zero_division=0)
    recall = recall_score(y, p, zero_division=0)
    fp = sum(1 for a,b in zip(y,p) if a == 0 and b == 1)
    fn = sum(1 for a,b in zip(y,p) if a == 1 and b == 0)
    print(f"\n{campo}: precision={precision:.3f}, cobertura={recall:.3f}, "
          f"falsos_positivos={fp}, falsos_negativos={fn}")
    por_caso = defaultdict(list)
    for caso, fila, umbral, predicho, correcto in resultados:
        por_caso[caso].append((predicho, correcto))
    for caso, valores in por_caso.items():
        aceptados = sum(p for p, _ in valores)
        relevantes = sum(v for _, v in valores)
        indicador = "RECHAZO" if aceptados == 0 else "MUESTRA"
        print(f"  {caso:15s} {indicador:8s} {aceptados}/5 "
              f"candidatos; {relevantes} etiquetados pertinentes/afines")
    return precision, recall, fp, fn


def main():
    filas = leer_archivo()
    if not RUTA_MODELO.is_dir():
        raise SystemExit("No existe MiniLM local. Ejecuta 12_probar_embeddings.py.")
    modelo = SentenceTransformer(str(RUTA_MODELO))

    grupos = defaultdict(list)
    for fila in filas:
        grupos[fila["caso"]].append(fila)

    print(f"Evaluacion experimental: {len(grupos)} preguntas, {len(filas)} candidatos")
    print("MiniLM original vs enfoque tematico; no se instalara otro modelo.")
    print("Etiquetas: 2=directa, 1=afin, 0=no pertinente.")
    print("No se evalua si el plan de estudios real cubre la actividad.")

    evaluadas = []
    for caso, grupo in grupos.items():
        pregunta = grupo[0]["pregunta"]
        tema = extraer_tema(pregunta)
        print(f"\n[{caso}] Tema extraido: {tema}")
        entrada = [
            {"nombre": f["programa"], "similitud": float(f["similitud"])}
            for f in grupo
        ]
        puntuadas = comparar_enfoques(pregunta, entrada, modelo)
        for original, nueva in zip(grupo, puntuadas):
            fila = dict(original)
            fila["tema_extraido"] = nueva["tema_extraido"]
            fila["similitud_focal"] = round(nueva["similitud_focal"], 6)
            fila["puntuacion_conservadora"] = round(
                nueva["puntuacion_conservadora"], 6
            )
            evaluadas.append(fila)

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("w", newline="", encoding="utf-8-sig") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=list(evaluadas[0]))
        writer.writeheader()
        writer.writerows(evaluadas)

    print("\nEVALUACION: umbral calibrado con 11 preguntas; prueba en la 12a.")
    resumen = {}
    for campo in CAMPOS:
        predicciones = validar_dejando_fuera_preguntas(evaluadas, campo)
        resumen[campo] = mostrar_resultados(predicciones, campo)

    print("\nArchivo creado:", SALIDA)
    print("IMPORTANTE: Estos umbrales cambian en cada prueba. NO se aplican a app.py.")
    print("Las etiquetas son propuestas revisables; falta probar nuevas preguntas.")
    print("Ninguna oferta, peso de MiniLM, ni archivo existente fue modificado.")


if __name__ == "__main__":
    main()
