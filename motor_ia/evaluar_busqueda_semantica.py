"""Diagnostico reproducible de recuperacion semantica (sin cambiar app.py).

Ejecutar desde la raiz de ProyectoIA:
    .\.venv\Scripts\python.exe motor_ia\evaluar_busqueda_semantica.py

Salida: resultados en datos/evaluacion_semantica_diagnostico.csv
"""

import csv
from pathlib import Path

from sentence_transformers import SentenceTransformer
from busqueda_semantica import cargar_programas, buscar_semanticamente, RUTA_MODELO, RAIZ
from entidades import conectar_bd

# Etiqueta de referencia para inspeccion MANUAL, no para asignar pertinencia automatica.
# 'relacionada' = deberia tener carreras afines; 'incierta' = evaluar la cobertura.
CONSULTAS = [
    ("videojuegos", "relacionada", "Me gustaría desarrollar videojuegos y programar mundos virtuales"),
    ("robotica", "relacionada", "Me interesa diseñar circuitos electrónicos y construir robots"),
    ("psicologia", "relacionada", "Me interesa estudiar el comportamiento humano y ayudar a personas con problemas emocionales"),
    ("derecho", "relacionada", "Quiero trabajar con leyes y defender los derechos de las personas"),
    ("arquitectura", "relacionada", "Me gustaría diseñar edificios y espacios habitables"),
    ("administracion", "relacionada", "Me interesa gestionar empresas y organizar negocios"),
    ("espacio", "incierta", "Me interesa investigar planetas y explorar el espacio exterior"),
    ("aeroespacial", "incierta", "Quiero diseñar cohetes y naves espaciales"),
    ("indecision", "incierta", "Quiero estudiar algo, pero todavía no sé qué"),
    ("trivial", "incierta", "Hola, ¿cómo estás hoy?"),
    ("meteorologia", "incierta", "Quiero pronosticar huracanes y estudiar la atmósfera"),
    ("arqueologia", "incierta", "Me gustaría excavar fósiles y estudiar dinosaurios"),
]


def main():
    print("DIAGNOSTICO DE BUSQUEDA SEMANTICA - MINILM")
    if not (RUTA_MODELO / "modules.json").exists():
        print("No se encontro MiniLM en modelos_ia/minilm.")
        print("Ejecuta primero motor_ia/12_probar_embeddings.py")
        return

    modelo = SentenceTransformer(str(RUTA_MODELO))
    with conectar_bd() as conexion:
        programas = cargar_programas(conexion)

    nombres = [nombre for _, nombre in programas]
    vectores = modelo.encode(nombres, convert_to_tensor=True, show_progress_bar=True)
    print(f"Programas cargados: {len(programas)}")

    filas = []
    for clave, grupo, pregunta in CONSULTAS:
        resultados = buscar_semanticamente(pregunta, modelo, programas, vectores, limite=5)
        print(f"\n[{clave}] {pregunta}")
        for posicion, resultado in enumerate(resultados, start=1):
            similitud = resultado["similitud"]
            print(f"  {posicion}. {resultado['nombre']} - {similitud:.4f}")
            filas.append({
                "caso": clave,
                "grupo": grupo,
                "pregunta": pregunta,
                "posicion": posicion,
                "id_programa": resultado["id_programa"],
                "programa": resultado["nombre"],
                "similitud": f"{similitud:.6f}",
                "pertinente_manual": "",  # completar con 1=si, 0=no o ?=dudoso
            })

    destino = RAIZ / "datos" / "evaluacion_semantica_diagnostico.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)
    print(f"\nArchivo generado: {destino}")
    print("IMPORTANTE: revisar y etiquetar 'pertinente_manual' antes de elegir umbrales.")


if __name__ == "__main__":
    main()
