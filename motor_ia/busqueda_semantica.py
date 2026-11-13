
from pathlib import Path

from sentence_transformers import SentenceTransformer, util
from entidades import conectar_bd


# Ubicacion del modelo descargado.
RAIZ = Path(__file__).resolve().parent.parent
RUTA_MODELO = RAIZ / "modelos_ia" / "minilm"


# Recuperar programas con ofertas educativas.
def cargar_programas(conexion):
    consulta = """
        SELECT DISTINCT
            pa.id_programa,
            pa.nombre
        FROM catalogo.programa_academico pa
        JOIN catalogo.oferta_educativa o
            ON o.id_programa = pa.id_programa
        ORDER BY pa.nombre
    """

    with conexion.cursor() as cursor:
        cursor.execute(consulta)
        return cursor.fetchall()


# Buscar programas por similitud semantica.
def buscar_semanticamente(pregunta, modelo, programas, vectores, limite=10):
    vector_pregunta = modelo.encode(
        pregunta,
        convert_to_tensor=True
    )

    similitudes = util.cos_sim(
        vector_pregunta,
        vectores
    )[0]

    cantidad = min(limite, len(programas))
    indices = similitudes.topk(k=cantidad).indices.tolist()

    resultados = []

    for indice in indices:
        id_programa, nombre = programas[indice]

        resultados.append({
            "id_programa": id_programa,
            "nombre": nombre,
            "similitud": float(similitudes[indice])
        })

    return resultados


def main():
    print("=" * 60)
    print("OFERTA EDUCATIVA CIUDAD DE MEXICO 2.0")
    print("Busqueda semantica con MiniLM")
    print("=" * 60)

    modelo = SentenceTransformer(str(RUTA_MODELO))
    print("\nModelo MiniLM cargado correctamente.")

    with conectar_bd() as conexion:
        programas = cargar_programas(conexion)

    print(f"Programas cargados: {len(programas)}")

    nombres = [
        nombre for id_programa, nombre in programas
    ]

    # Calcular los embeddings del catalogo una sola vez.
    vectores = modelo.encode(
        nombres,
        convert_to_tensor=True,
        show_progress_bar=True
    )

    print("\nEmbeddings del catalogo generados.")

    while True:
        pregunta = input(
            "\nDescribe tus intereses (o 'salir'): "
        ).strip()

        if pregunta.lower() == "salir":
            break

        if not pregunta:
            continue

        resultados = buscar_semanticamente(
            pregunta,
            modelo,
            programas,
            vectores
        )

        print("\nPROGRAMAS MAS SIMILARES:")

        for posicion, resultado in enumerate(resultados, start=1):
            print(
                f"{posicion}. "
                f"[ID {resultado['id_programa']}] "
                f"{resultado['nombre']} | "
                f"Similitud: {resultado['similitud']:.4f}"
            )


if __name__ == "__main__":
    main()
