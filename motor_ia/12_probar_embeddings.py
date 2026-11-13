
from pathlib import Path
from sentence_transformers import SentenceTransformer, util

# Localizar la carpeta principal del proyecto.
RAIZ = Path(__file__).resolve().parent.parent

# Carpeta donde guardaremos el modelo.
RUTA_MODELO = RAIZ / "modelos_ia" / "minilm"

# Nombre del modelo preentrenado.
NOMBRE_MODELO = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


# Cargar o descargar el modelo.
def cargar_modelo():
    if (RUTA_MODELO / "modules.json").exists():
        print("Cargando modelo desde la computadora...")
        modelo = SentenceTransformer(str(RUTA_MODELO))
    else:
        print("Descargando modelo preentrenado...")
        modelo = SentenceTransformer(NOMBRE_MODELO)

        # Guardar los archivos para futuros usos.
        modelo.save(str(RUTA_MODELO))
        print("Modelo guardado correctamente.")

    return modelo


# Probar los embeddings.
def main():
    print("=" * 60)
    print("OFERTA EDUCATIVA CIUDAD DE MEXICO 2.0")
    print("Prueba de embeddings con MiniLM")
    print("=" * 60)

    modelo = cargar_modelo()

    textos = [
        "Me interesa desarrollar videojuegos",
        "Ingenieria en Desarrollo de Software",
        "Licenciatura en Derecho"
    ]

    # Convertir los textos en vectores numericos.
    vectores = modelo.encode(
        textos,
        convert_to_tensor=True
    )

    print("\nCantidad de textos:", len(textos))
    print("Dimensiones de cada vector:", vectores.shape[1])

    # Calcular la similitud del coseno.
    similitud = util.cos_sim(vectores, vectores)

    print("\nSIMILITUDES:")

    for i in range(len(textos)):
        for j in range(i + 1, len(textos)):
            print(f"\nTexto A: {textos[i]}")
            print(f"Texto B: {textos[j]}")
            print(f"Similitud: {similitud[i][j].item():.4f}")


if __name__ == "__main__":
    main()
