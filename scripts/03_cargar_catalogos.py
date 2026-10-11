"""Carga inicial de catálogos para el proyecto Oferta Educativa.

Origen: origen.registro_origen (JSONB).
Alcance: estados, niveles y modalidades nacionales; programas de LICENCIATURA CDMX.
No modifica los registros de origen ni crea ofertas, instituciones o planteles.
Ejecutar desde ProyectoIA con: python scripts/03_cargar_catalogos.py
"""

from getpass import getpass

import psycopg2
from psycopg2.extras import execute_values


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "oferta_educativa",
    "user": "postgres",
}


def cargar():
    password = getpass("Contraseña PostgreSQL para postgres: ")
    conexion = psycopg2.connect(**DB_CONFIG, password=password)

    try:
        with conexion:
            with conexion.cursor() as cur:
                # Evitar crear catálogos a partir de campos vacíos.
                cur.execute("""
                    SELECT DISTINCT btrim(datos_json->>'estado')
                    FROM origen.registro_origen
                    WHERE NULLIF(btrim(datos_json->>'estado'), '') IS NOT NULL
                    ORDER BY 1
                """)
                estados = [r[0] for r in cur.fetchall()]

                cur.execute("""
                    SELECT DISTINCT btrim(datos_json->>'nivel_estudios')
                    FROM origen.registro_origen
                    WHERE NULLIF(btrim(datos_json->>'nivel_estudios'), '') IS NOT NULL
                    ORDER BY 1
                """)
                niveles = [r[0] for r in cur.fetchall()]

                cur.execute("""
                    SELECT DISTINCT btrim(datos_json->>'modalidad')
                    FROM origen.registro_origen
                    WHERE NULLIF(btrim(datos_json->>'modalidad'), '') IS NOT NULL
                    ORDER BY 1
                """)
                modalidades = [r[0] for r in cur.fetchall()]

                # Evitar problemas de codificación de acentos al escribir SQL en consola.
                cur.execute("""
                    SELECT DISTINCT btrim(datos_json->>'programa')
                    FROM origen.registro_origen
                    WHERE btrim(datos_json->>'estado') =
                          'CIUDAD DE M' || chr(201) || 'XICO'
                      AND btrim(datos_json->>'nivel_estudios') = 'LICENCIATURA'
                      AND NULLIF(btrim(datos_json->>'programa'), '') IS NOT NULL
                    ORDER BY 1
                """)
                programas = [r[0] for r in cur.fetchall()]

                print(f"Estados distintos en origen: {len(estados)}")
                print(f"Niveles distintos en origen: {len(niveles)}")
                print(f"Modalidades distintas en origen: {len(modalidades)}")
                print(f"Programas distintos de licenciatura CDMX: {len(programas)}")

                # Validaciones del dataset que ya auditamos.
                niveles_esperados = {
                    'LICENCIATURA', 'MAESTRÍA', 'ESPECIALIDAD', 'DOCTORADO',
                    'TÉCNICO SUPERIOR UNIVERSITARIO', 'PROFESIONAL ASOCIADO'
                }
                modalidades_esperadas = {
                    'ESCOLARIZADA', 'MIXTA', 'NO ESCOLARIZADA'
                }
                if set(niveles) != niveles_esperados:
                    raise ValueError(f"Niveles no coinciden con los esperados: {niveles}")
                if set(modalidades) != modalidades_esperadas:
                    raise ValueError(f"Modalidades no coinciden con las esperadas: {modalidades}")
                if len(programas) != 588:
                    raise ValueError(
                        f"Se esperaban 588 nombres de programas CDMX, aparecieron {len(programas)}."
                    )

                execute_values(
                    cur,
                    "INSERT INTO catalogo.estado (nombre) VALUES %s ON CONFLICT (nombre) DO NOTHING",
                    [(e,) for e in estados],
                )
                execute_values(
                    cur,
                    "INSERT INTO catalogo.nivel_academico (nombre) VALUES %s ON CONFLICT (nombre) DO NOTHING",
                    [(n,) for n in niveles],
                )
                execute_values(
                    cur,
                    "INSERT INTO catalogo.modalidad (nombre) VALUES %s ON CONFLICT (nombre) DO NOTHING",
                    [(m,) for m in modalidades],
                )

                # Resolución de FK al nivel LICENCIATURA.
                cur.execute(
                    "SELECT id_nivel FROM catalogo.nivel_academico WHERE nombre = %s",
                    ('LICENCIATURA',),
                )
                nivel = cur.fetchone()
                if nivel is None:
                    raise ValueError("No se encontró el nivel LICENCIATURA")
                id_nivel = nivel[0]

                execute_values(
                    cur,
                    """INSERT INTO catalogo.programa_academico (nombre, id_nivel)
                       VALUES %s ON CONFLICT (nombre, id_nivel) DO NOTHING""",
                    [(p, id_nivel) for p in programas],
                )

                cur.execute("SELECT COUNT(*) FROM catalogo.programa_academico WHERE id_nivel=%s", (id_nivel,))
                total_programas = cur.fetchone()[0]
                if total_programas < len(programas):
                    raise ValueError("No se conservaron todos los programas esperados")

                for tabla in ('estado', 'nivel_academico', 'modalidad', 'programa_academico'):
                    cur.execute(f'SELECT COUNT(*) FROM catalogo.{tabla}')
                    print(f"catalogo.{tabla}: {cur.fetchone()[0]} filas")

        print("Carga confirmada. Es seguro volver a ejecutar este script.")
    finally:
        conexion.close()


if __name__ == '__main__':
    try:
        cargar()
    except (psycopg2.Error, ValueError) as exc:
        print(f"ERROR: carga cancelada y transacción revertida: {exc}")
        raise SystemExit(1)
