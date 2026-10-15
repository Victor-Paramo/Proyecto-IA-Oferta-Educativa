
import sys
from pathlib import Path

from sentence_transformers import SentenceTransformer

# Localizar las carpetas del proyecto.
RAIZ = Path(__file__).resolve().parent.parent
CARPETA_MOTOR = RAIZ / "motor_ia"

# Permitir reutilizar los modulos existentes.
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(CARPETA_MOTOR))

from entidades import conectar_bd

from busqueda_semantica import (
    cargar_programas,
    buscar_semanticamente,
    RUTA_MODELO
)

from funciones.buscar_programa import buscar_programa


# Recuperar ofertas de los programas encontrados por MiniLM.
def recuperar_ofertas(conexion, candidatos):
    resultados = []

    for candidato in candidatos:
        ofertas = buscar_programa(
            conexion,
            id_programa=candidato["id_programa"]
        )

        # Contar instituciones diferentes.
        instituciones = {
            oferta["institucion"]
            for oferta in ofertas
        }

        resultados.append({
            "id_programa": candidato["id_programa"],
            "programa": candidato["nombre"],
            "similitud": candidato["similitud"],
            "total_ofertas": len(ofertas),
            "total_instituciones": len(instituciones),
            "ofertas": ofertas
        })

    return resultados


def main():
    print("=" * 60)
    print("OFERTA EDUCATIVA CIUDAD DE MEXICO 2.0")
    print("Busqueda semantica y recuperacion de ofertas")
    print("=" * 60)

    # Cargar MiniLM desde nuestra computadora.
    modelo = SentenceTransformer(str(RUTA_MODELO))
    print("\nModelo MiniLM cargado correctamente.")

    with conectar_bd() as conexion:
        # Recuperar las carreras reales de PostgreSQL.
        programas = cargar_programas(conexion)

        nombres = [
            nombre for id_programa, nombre in programas
        ]

        print(f"Programas cargados: {len(programas)}")

        # Generar los embeddings del catalogo una sola vez.
        vectores = modelo.encode(
            nombres,
            convert_to_tensor=True,
            show_progress_bar=True
        )

        print("\nSistema de recuperacion preparado.")

        while True:
            pregunta = input(
                "\nDescribe tus intereses (o 'salir'): "
            ).strip()

            if pregunta.lower() == "salir":
                break

            if not pregunta:
                continue

            # Primera etapa: encontrar programas relacionados.
            candidatos = buscar_semanticamente(
                pregunta,
                modelo,
                programas,
                vectores,
                limite=5
            )

            # Segunda etapa: recuperar ofertas verificables.
            resultados = recuperar_ofertas(
                conexion,
                candidatos
            )

            print("\nRESULTADOS DE LA BUSQUEDA:")

            for posicion, resultado in enumerate(
                resultados, start=1
            ):
                print("\n" + "-" * 55)
                print(f"{posicion}. {resultado['programa']}")
                print(f"ID programa: {resultado['id_programa']}")
                print(f"Similitud: {resultado['similitud']:.4f}")
                print(f"Ofertas: {resultado['total_ofertas']}")
                print(
                    "Instituciones diferentes:",
                    resultado["total_instituciones"]
                )

                if not resultado["ofertas"]:
                    print("No se encontraron ofertas.")
                    continue

                # Mostrar las primeras cinco ofertas del programa.
                for oferta in resultado["ofertas"][:5]:
                    print(
                        f"  - {oferta['institucion']} | "
                        f"{oferta['plantel'] or 'No especificado'} | "
                        f"{oferta['modalidad']}"
                    )

                if resultado["total_ofertas"] > 5:
                    print(
                        f"  Mostrando 5 de "
                        f"{resultado['total_ofertas']} ofertas."
                    )


if __name__ == "__main__":
    main()
