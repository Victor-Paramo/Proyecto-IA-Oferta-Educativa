"""Carga inicial de registros documentales de oferta educativa a PostgreSQL.

Ejecutar desde la raíz del proyecto:
    python scripts/cargar_registros_origen.py

Requiere: pip install psycopg2-binary
"""

import json
import os
from collections import Counter
from getpass import getpass
from pathlib import Path

import psycopg2
from psycopg2.extras import Json, execute_values


RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO = RAIZ / "datos" / "oferta_educativa_limpia.json"
TOTAL_ESPERADO = 27054
TAMANO_LOTE = 500


def nombre_fuente(registro):
    valor = registro.get("fuente")
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError("Hay registros sin campo 'fuente' válido.")
    return Path(valor.replace("\\", "/")).name.strip()


def numero_pagina(registro):
    valor = registro.get("pagina")
    if valor in (None, ""):
        return None
    try:
        pagina = int(valor)
    except (ValueError, TypeError):
        return None  # El valor original permanece en datos_json.
    return pagina if pagina > 0 else None


def main():
    if not ARCHIVO.is_file():
        raise FileNotFoundError(f"No se encontró el archivo: {ARCHIVO}")

    with ARCHIVO.open("r", encoding="utf-8") as archivo:
        registros = json.load(archivo)

    if not isinstance(registros, list) or not all(isinstance(r, dict) for r in registros):
        raise ValueError("Se esperaba una lista JSON de objetos.")
    if len(registros) != TOTAL_ESPERADO:
        raise ValueError(
            f"Se esperaban {TOTAL_ESPERADO} registros; se encontraron {len(registros)}. "
            "Se cancela la carga para revisar la fuente."
        )

    fuentes = Counter(nombre_fuente(r) for r in registros)
    print(f"Archivo: {ARCHIVO}")
    print(f"Registros validados: {len(registros):,}")
    print("Documentos fuente:")
    for fuente, total in sorted(fuentes.items()):
        print(f"  {fuente}: {total:,}")

    usuario = os.getenv("PGUSER", "postgres")
    contrasena = os.getenv("PGPASSWORD") or getpass(f"Contraseña PostgreSQL para {usuario}: ")
    conexion = psycopg2.connect(
        dbname="oferta_educativa",
        user=usuario,
        password=contrasena,
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
    )

    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM origen.registro_origen")
            existentes = cursor.fetchone()[0]
            if existentes:
                raise RuntimeError(
                    f"La tabla origen.registro_origen ya tiene {existentes} filas. "
                    "Se cancela para evitar una segunda carga duplicada."
                )

            ids_documentos = {}
            for fuente in sorted(fuentes):
                cursor.execute(
                    """
                    INSERT INTO origen.documento_fuente (nombre_archivo)
                    VALUES (%s)
                    ON CONFLICT (nombre_archivo)
                    DO UPDATE SET nombre_archivo = EXCLUDED.nombre_archivo
                    RETURNING id_documento
                    """,
                    (fuente,),
                )
                ids_documentos[fuente] = cursor.fetchone()[0]

            total_insertado = 0
            for inicio in range(0, len(registros), TAMANO_LOTE):
                lote = registros[inicio:inicio + TAMANO_LOTE]
                filas = [
                    (
                        ids_documentos[nombre_fuente(r)],
                        numero_pagina(r),
                        Json(r, dumps=lambda d: json.dumps(d, ensure_ascii=False)),
                    )
                    for r in lote
                ]
                execute_values(
                    cursor,
                    """
                    INSERT INTO origen.registro_origen
                        (id_documento, pagina, datos_json)
                    VALUES %s
                    """,
                    filas,
                    page_size=TAMANO_LOTE,
                )
                total_insertado += len(filas)
                print(f"Cargados: {total_insertado:,}/{TOTAL_ESPERADO:,}", end="\r")

            cursor.execute("SELECT COUNT(*) FROM origen.registro_origen")
            total_bd = cursor.fetchone()[0]
            if total_bd != TOTAL_ESPERADO:
                raise RuntimeError(
                    f"Conteo inesperado: {total_bd} filas. Se cancela la transacción."
                )

        conexion.commit()
        print(f"\nCarga confirmada: {total_bd:,} registros en origen.registro_origen.")
        print(f"Documentos fuente relacionados: {len(ids_documentos)}")
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


if __name__ == "__main__":
    main()
