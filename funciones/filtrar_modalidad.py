
import sys
from pathlib import Path

# Permitir importar el modulo de conexion existente.
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "motor_ia"))

from entidades import conectar_bd


# Buscar ofertas educativas por modalidad.
def filtrar_modalidad(conexion, modalidad):
    consulta = """
        SELECT
            o.id_oferta,
            i.nombre AS institucion,
            p.nombre AS plantel,
            pa.nombre AS programa,
            m.nombre AS modalidad
        FROM catalogo.oferta_educativa o
        JOIN catalogo.plantel p
            ON p.id_plantel = o.id_plantel
        JOIN catalogo.institucion i
            ON i.id_institucion = p.id_institucion
        JOIN catalogo.programa_academico pa
            ON pa.id_programa = o.id_programa
        JOIN catalogo.modalidad m
            ON m.id_modalidad = o.id_modalidad
        WHERE m.nombre = %s
        ORDER BY i.nombre, pa.nombre, p.nombre, o.id_oferta
    """

    with conexion.cursor() as cursor:
        cursor.execute(consulta, (modalidad,))

        columnas = [columna[0] for columna in cursor.description]
        registros = cursor.fetchall()

    return [
        dict(zip(columnas, registro))
        for registro in registros
    ]


# Programa principal para probar la funcion.
def main():
    print("=" * 60)
    print("OFERTA EDUCATIVA CIUDAD DE MEXICO 2.0")
    print("Bloque 3: Filtro por modalidad")
    print("=" * 60)

    with conectar_bd() as conexion:
        print("\nConexion establecida con PostgreSQL.")

        resultados = filtrar_modalidad(
            conexion,
            modalidad="NO ESCOLARIZADA"
        )

        print(f"\nOfertas encontradas: {len(resultados)}")

        for oferta in resultados[:15]:
            print("\nInstitucion:", oferta["institucion"])
            print("Plantel:", oferta["plantel"] or "No especificado")
            print("Programa:", oferta["programa"])
            print("Modalidad:", oferta["modalidad"])


if __name__ == "__main__":
    main()
