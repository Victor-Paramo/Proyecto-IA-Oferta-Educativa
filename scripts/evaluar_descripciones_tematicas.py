"""Compara MiniLM sobre nombres originales vs nombres con temas auxiliares.

Prueba solo lectura. No modifica app.py, tablas PostgreSQL ni pesos del modelo.
ATENCION: Los nuevos top-5 requieren nuevas etiquetas manuales; NO calculamos
una precision ficticia reutilizando etiquetas de carreras diferentes.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

from sentence_transformers import SentenceTransformer, util

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "motor_ia"))
from entidades import conectar_bd
from busqueda_semantica import cargar_programas, RUTA_MODELO
from descripciones_tematicas import describir_por_nombre

DATOS = RAIZ / "datos"
ETIQUETAS = DATOS / "evaluacion_semantica_escala_0_2.csv"
SALIDA = DATOS / "comparacion_descripciones_tematicas.csv"
CAMPOS = (
    "caso", "pregunta", "metodo", "posicion", "id_programa", "programa",
    "similitud", "areas_auxiliares", "etiqueta_0_2", "estado_etiqueta"
)


def cargar_diagnostico():
    if not ETIQUETAS.is_file():
        raise SystemExit(f"No se encuentra el archivo: {ETIQUETAS}")
    with ETIQUETAS.open(encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    requeridas = {"caso", "pregunta", "id_programa", "pertinencia_0_2"}
    if not filas or not requeridas.issubset(filas[0]):
        raise SystemExit("El CSV debe contener caso, pregunta, id_programa y pertinencia_0_2")
    preguntas = {}
    etiquetas = {}
    for fila in filas:
        preguntas[fila["caso"]] = fila["pregunta"]
        etiquetas[(fila["caso"], int(fila["id_programa"]))] = fila["pertinencia_0_2"]
    return preguntas, etiquetas


def top5(vector_pregunta, vectores_catalogo, catalogo, areas, caso, pregunta, metodo, etiquetas):
    scores = util.cos_sim(vector_pregunta, vectores_catalogo)[0]
    indices = scores.topk(k=min(5, len(catalogo))).indices.tolist()
    resultado = []
    for posicion, indice in enumerate(indices, 1):
        id_programa, nombre = catalogo[indice]
        llave = (caso, int(id_programa))
        tiene_etiqueta = llave in etiquetas
        resultado.append({
            "caso": caso,
            "pregunta": pregunta,
            "metodo": metodo,
            "posicion": posicion,
            "id_programa": id_programa,
            "programa": nombre,
            "similitud": f"{float(scores[indice]):.6f}",
            "areas_auxiliares": ";".join(areas[indice]),
            "etiqueta_0_2": etiquetas[llave] if tiene_etiqueta else "",
            "estado_etiqueta": "etiqueta previa (revisable)" if tiene_etiqueta else "PENDIENTE: candidato nuevo",
        })
    return resultado


def main():
    preguntas, etiquetas = cargar_diagnostico()
    if not RUTA_MODELO.is_dir():
        raise SystemExit("MiniLM no esta descargado. Ejecuta 12_probar_embeddings.py primero.")

    print("=" * 65)
    print("DIAGNOSTICO: TITULOS OFICIALES VS TEMAS AUXILIARES INFERIDOS")
    print("El experimento NO edita app.py, PostgreSQL ni los pesos MiniLM.")
    print("Las descripciones tematicas NO son documentos oficiales SEP.")
    print("=" * 65)

    modelo = SentenceTransformer(str(RUTA_MODELO))
    with conectar_bd() as conexion:
        catalogo = cargar_programas(conexion)
    if not catalogo:
        raise SystemExit("No se encontraron programas academicos con ofertas.")

    titulos = [nombre for _, nombre in catalogo]
    procesados = [describir_por_nombre(nombre) for nombre in titulos]
    enriquecidos = [texto for texto, _ in procesados]
    areas = [etiquetas_area for _, etiquetas_area in procesados]
    total = sum(bool(a) for a in areas)
    print(f"Programas consultados: {len(catalogo)}")
    print(f"Con etiquetas tematicas inferidas del titulo: {total}")
    print(f"Sin etiquetas tematicas (titulo original): {len(catalogo) - total}")

    print("Calculando embeddings originales, enriquecidos y de preguntas...")
    vec_titulos = modelo.encode(titulos, convert_to_tensor=True, show_progress_bar=True)
    vec_enriquecidos = modelo.encode(enriquecidos, convert_to_tensor=True, show_progress_bar=True)
    casos = list(preguntas.items())
    vec_preguntas = modelo.encode([p for _, p in casos], convert_to_tensor=True)

    salida = []
    for idx, (caso, pregunta) in enumerate(casos):
        vec_pregunta = vec_preguntas[idx:idx+1]
        a = top5(vec_pregunta, vec_titulos, catalogo, areas, caso, pregunta,
                 "nombre_original", etiquetas)
        b = top5(vec_pregunta, vec_enriquecidos, catalogo, areas, caso, pregunta,
                 "nombre_enriquecido", etiquetas)
        salida.extend(a + b)
        ids_a = {int(f["id_programa"]) for f in a}
        ids_b = {int(f["id_programa"]) for f in b}
        nuevos = len(ids_b - ids_a)
        sin_etiqueta = sum(not f["etiqueta_0_2"].strip() for f in b)
        print(f"\n{caso.upper():15s} - {nuevos} candidatos NUEVOS; "
              f"{sin_etiqueta} etiquetas PENDIENTES en top5 enriquecido")
        if caso in {"videojuegos", "robotica", "psicologia", "espacio", "meteorologia"}:
            print("  ORIGINAL:")
            for f in a:
                print(f"    {f['posicion']}. {f['programa']} ({f['similitud']})")
            print("  ENRIQUECIDO:")
            for f in b:
                print(f"    {f['posicion']}. {f['programa']} ({f['similitud']})")

    SALIDA.parent.mkdir(exist_ok=True, parents=True)
    with SALIDA.open("w", encoding="utf-8-sig", newline="") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=CAMPOS)
        writer.writeheader()
        writer.writerows(salida)

    por_metodo = defaultdict(list)
    for f in salida:
        por_metodo[f["metodo"]].append(f)
    nuevos_totales = sum(f["estado_etiqueta"].startswith("PENDIENTE")
                        for f in por_metodo["nombre_enriquecido"])
    print("\nArchivo creado:", SALIDA)
    print(f"Filas: {len(salida)}; etiquetas NUEVAS por revisar: {nuevos_totales}")
    print("No compares NDCG/P@5 de la lista enriquecida hasta etiquetar sus nuevos candidatos.")
    print("Conservar preguntas nuevas para la evaluacion final independiente.")


if __name__ == "__main__":
    main()
