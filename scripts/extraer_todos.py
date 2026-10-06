import pdfplumber
import json
from pathlib import Path

carpeta_pdfs = Path(r"C:\Users\Admin\Desktop\ProyectoIA\PDFs")
carpeta_datos = Path(r"C:\Users\Admin\Desktop\ProyectoIA\datos")

archivos_pdf = sorted(carpeta_pdfs.glob("*.pdf"))

total_general = 0
total_cdmx = 0
total_licenciaturas_cdmx = 0

print("========================================")
print("EXTRACCION DE ARCHIVOS PDF")
print("========================================")
print()

print(f"PDF encontrados: {len(archivos_pdf)}")
print()

for archivo_pdf in archivos_pdf:

    print("----------------------------------------")
    print(f"Procesando: {archivo_pdf.name}")
    print("----------------------------------------")

    registros = []

    with pdfplumber.open(archivo_pdf) as pdf:

        print(f"Paginas: {len(pdf.pages)}")

        for numero_pagina, pagina in enumerate(pdf.pages, start=1):

            tablas = pagina.extract_tables()
            registros_pagina = 0

            for tabla in tablas:

                if not tabla or len(tabla) <= 1:
                    continue

                # Se omite el encabezado de la tabla
                for fila in tabla[1:]:

                    if len(fila) != 6:
                        continue

                    registro = {
                        "institucion": fila[0],
                        "estado": fila[1],
                        "nivel_estudios": fila[2],
                        "programa": fila[3],
                        "modalidad": fila[4],
                        "acuerdo_rvoe_fecha": fila[5],
                        "fuente": archivo_pdf.name,
                        "pagina": numero_pagina
                    }

                    registros.append(registro)
                    registros_pagina += 1

            print(
                f"Pagina {numero_pagina}: "
                f"{registros_pagina} registros"
            )

    # Crear un JSON bruto independiente para este PDF
    nombre_salida = archivo_pdf.stem + "_bruto.json"
    ruta_salida = carpeta_datos / nombre_salida

    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(
            registros,
            f,
            ensure_ascii=False,
            indent=4
        )

    # Conteos de este archivo
    cdmx_archivo = 0
    licenciaturas_cdmx_archivo = 0

    for registro in registros:

        estado = (
            (registro.get("estado") or "")
            .replace("\n", " ")
            .strip()
        )

        nivel = (
            (registro.get("nivel_estudios") or "")
            .replace("\n", " ")
            .strip()
        )

        if estado == "CIUDAD DE MÉXICO":
            cdmx_archivo += 1

            if nivel == "LICENCIATURA":
                licenciaturas_cdmx_archivo += 1

    total_general += len(registros)
    total_cdmx += cdmx_archivo
    total_licenciaturas_cdmx += licenciaturas_cdmx_archivo

    print()
    print(f"Registros guardados: {len(registros)}")
    print(f"Registros CDMX: {cdmx_archivo}")
    print(
        "Licenciaturas CDMX: "
        f"{licenciaturas_cdmx_archivo}"
    )
    print(f"JSON creado: {nombre_salida}")
    print()

print("========================================")
print("RESUMEN GENERAL")
print("========================================")
print(f"PDF procesados: {len(archivos_pdf)}")
print(f"TOTAL DE REGISTROS: {total_general}")
print(f"TOTAL CDMX: {total_cdmx}")
print(
    "TOTAL LICENCIATURAS CDMX: "
    f"{total_licenciaturas_cdmx}"
)
print("========================================")