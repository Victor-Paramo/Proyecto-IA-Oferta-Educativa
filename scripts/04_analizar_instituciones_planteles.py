"""Diagnóstico no destructivo de instituciones y posibles planteles en CDMX.

Ejecutar desde la raíz del proyecto:
    python scripts/04_analizar_instituciones_planteles.py

No modifica PostgreSQL. Produce archivos CSV en datos/.
"""
from __future__ import annotations

import csv
import getpass
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "datos"
OUTPUT.mkdir(exist_ok=True)

# Son señales para revisión humana, NO reglas de separación automática.
CAMPUS = re.compile(r"\b(?:CAMPUS|PLANTEL|SEDE|UNIDAD|EXTENSI[ÓO]N)\b", re.I)


def main() -> None:
    password = os.getenv("PGPASSWORD") or getpass.getpass("Contraseña PostgreSQL para postgres: ")
    conn = psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "oferta_educativa"),
        user=os.getenv("PGUSER", "postgres"),
        password=password,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    BTRIM(datos_json->>'institucion') AS institucion,
                    COUNT(*) AS registros,
                    COUNT(DISTINCT datos_json->>'programa') AS programas,
                    COUNT(DISTINCT datos_json->>'modalidad') AS modalidades
                FROM origen.registro_origen
                WHERE datos_json->>'estado' = %s
                  AND datos_json->>'nivel_estudios' = 'LICENCIATURA'
                GROUP BY BTRIM(datos_json->>'institucion')
                ORDER BY COUNT(*) DESC, BTRIM(datos_json->>'institucion');
            """, ("CIUDAD DE MÉXICO",))
            rows = cur.fetchall()
        conteo = sum(int(r[1]) for r in rows)
        if conteo != 2810:
            raise RuntimeError(f"Se esperaban 2810 registros de licenciatura CDMX; se obtuvieron {conteo}.")

        out = OUTPUT / "diagnostico_instituciones_cdmx.csv"
        with out.open("w", encoding="utf-8-sig", newline="") as fp:
            writer = csv.writer(fp)
            writer.writerow(["nombre_en_pdf", "registros", "programas_distintos", "modalidades_distintas", "indicio_de_plantel", "revision"])
            for nombre, registros, programas, modalidades in rows:
                texto = nombre or ""
                indicio = "SI" if CAMPUS.search(texto) else "NO"
                writer.writerow([texto, registros, programas, modalidades, indicio, "PENDIENTE"])

        print(f"Registros licenciatura CDMX: {conteo:,}")
        print(f"Nombres de institucion distintos (incluido eventual vacio): {len(rows)}")
        print(f"Nombres con indicador CAMPUS/PLANTEL/SEDE/UNIDAD/EXTENSION: {sum(bool(CAMPUS.search(r[0] or '')) for r in rows)}")
        print(f"Nombres vacíos: {sum(not (r[0] or '').strip() for r in rows)}")
        print(f"CSV generado: {out}")
        print("No se modificó ninguna tabla de PostgreSQL.")
        print("\nEjemplos de nombres que requieren revisión:")
        ejemplos = [r[0] for r in rows if CAMPUS.search(r[0] or "")][:12]
        for nombre in ejemplos:
            print(f"  - {nombre}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
