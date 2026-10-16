"""Experimento de cobertura semántica: NO modifica app.py ni los modelos.

Utiliza nombres de los programas existentes y las mismas preguntas de la
prueba anterior; los resultados se guardan para revisión humana.
"""
import csv
import sys
from pathlib import Path

from sentence_transformers import SentenceTransformer, util

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "motor_ia"))

from motor_ia.entidades import conectar_bd
from motor_ia.busqueda_semantica import cargar_programas, RUTA_MODELO
from motor_ia.descripciones_tematicas import describir_por_nombre
from motor_ia.validacion_cobertura_tematica import (
    construir_indice, comprobar_cobertura,
)

ENTRADA = RAIZ / "datos" / "evaluacion_semantica_escala_0_2.csv"
SALIDA = RAIZ / "datos" / "diagnostico_cobertura_tematica.csv"

PRUEBAS_NUEVAS = {
    "nuevo_codigo_movil": "Quiero programar aplicaciones para celulares",
    "nuevo_robots": "Quiero automatizar robots en una fábrica",
    "nuevo_derecho": "Me interesa defender derechos laborales",
    "nuevo_cocina": "Quiero aprender a cocinar postres",
    "nuevo_cosmos": "Quiero observar exoplanetas y estrellas lejanas",
    "nuevo_clima": "Me interesa pronosticar huracanes en el Caribe",
    "nuevo_indefinida": "No sé qué estudiar, ¿me ayudas?",
    "nuevo_paleontologia": "Quiero investigar fósiles antiguos",
}


def leer_preguntas():
    if not ENTRADA.is_file():
        raise SystemExit(f"Falta el archivo de diagnóstico: {ENTRADA}")
    with ENTRADA.open(encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    if not filas or not {"caso", "pregunta"}.issubset(filas[0]):
        raise SystemExit("CSV sin columnas 'caso' y 'pregunta'")
    preguntas = {}
    for fila in filas:
        preguntas[fila["caso"]] = fila["pregunta"]
    return preguntas


def main():
    print("=" * 62)
    print("DIAGNÓSTICO: COMPROBACIÓN DE COBERTURA TEMÁTICA")
    print("=" * 62)
    print("No modifica app.py, la base de datos ni los pesos MiniLM.")

    preguntas = leer_preguntas()
    preguntas.update(PRUEBAS_NUEVAS)

    with conectar_bd() as conexion:
        programas = cargar_programas(conexion)
    indice = construir_indice(programas)
    print(f"Programas encontrados: {len(programas)}")
    print("Temas con títulos registrados:")
    print(" | ".join(f"{tema}: {len(filas)}" for tema, filas in sorted(indice.items())))

    print("\nPreparando MiniLM para ordenar candidatos con tema explícito...")
    modelo = SentenceTransformer(str(RUTA_MODELO))
    nombres = [nombre for _, nombre in programas]
    enriquecidos = [describir_por_nombre(nombre)[0] for nombre in nombres]
    vectores = modelo.encode(enriquecidos, convert_to_tensor=True, show_progress_bar=True)

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    campos = ("caso", "pregunta", "estado", "temas", "cantidad_titulos_directos",
              "posicion", "id_programa", "programa", "similitud", "etiqueta_manual")
    etiquetas = {}
    with ENTRADA.open(encoding="utf-8-sig", newline="") as archivo:
        for fila in csv.DictReader(archivo):
            etiquetas[(fila["caso"], int(fila["id_programa"]))] = fila["pertinencia_0_2"]

    with SALIDA.open("w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        for caso, pregunta in preguntas.items():
            cobertura = comprobar_cobertura(pregunta, indice)
            validos = cobertura["ids_validos"]
            print(f"\n[{caso}] {pregunta}")
            print(f"  Temas: {', '.join(cobertura['temas']) or '(sin tema)'}")
            print(f"  Estado: {cobertura['estado']} | Programas directos: {len(validos)}")

            resultados = []
            if validos:
                vector_pregunta = modelo.encode(pregunta, convert_to_tensor=True)
                similitudes = util.cos_sim(vector_pregunta, vectores)[0]
                indices = [i for i, (id_programa, _) in enumerate(programas)
                           if int(id_programa) in validos]
                indices.sort(key=lambda i: float(similitudes[i]), reverse=True)
                for i in indices[:5]:
                    id_programa, nombre = programas[i]
                    resultados.append((int(id_programa), nombre, float(similitudes[i])))
                    print(f"    {nombre}  |  {float(similitudes[i]):.4f}")
            else:
                print("   ", cobertura["mensaje"])

            if not resultados:
                escritor.writerow({
                    "caso": caso, "pregunta": pregunta, "estado": cobertura["estado"],
                    "temas": ";".join(cobertura["temas"]),
                    "cantidad_titulos_directos": len(validos),
                })
            for pos, (id_programa, nombre, similitud) in enumerate(resultados, 1):
                escritor.writerow({
                    "caso": caso, "pregunta": pregunta, "estado": cobertura["estado"],
                    "temas": ";".join(cobertura["temas"]),
                    "cantidad_titulos_directos": len(validos),
                    "posicion": pos, "id_programa": id_programa, "programa": nombre,
                    "similitud": f"{similitud:.6f}",
                    # Si la carrera no fue evaluada previamente, NO inventar etiqueta.
                    "etiqueta_manual": etiquetas.get((caso, id_programa), ""),
                })
    print(f"\nDiagnóstico guardado en: {SALIDA}")
    print("Las etiquetas vacías requieren revisión humana.")
    print("No incorpora cambios en el asistente: es solo una prueba.")


if __name__ == "__main__":
    main()
