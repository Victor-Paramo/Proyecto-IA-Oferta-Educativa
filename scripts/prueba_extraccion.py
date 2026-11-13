import pdfplumber
import json

archivo = r"C:\Users\Admin\Desktop\ProyectoIA\PDFs\VIG_fed_A-C_.pdf"
salida = r"C:\Users\Admin\Desktop\ProyectoIA\datos\VIG_fed_A-C_bruto.json"

registros = []

with pdfplumber.open(archivo) as pdf:

    for numero_pagina, pagina in enumerate(pdf.pages, start=1):

        tablas = pagina.extract_tables()

        registros_pagina = 0

        for tabla in tablas:

            # Saltamos el encabezado
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
                    "fuente": "VIG_fed_A-C_.pdf",
                    "pagina": numero_pagina
                }

                registros.append(registro)
                registros_pagina += 1

        print(
            f"Pagina {numero_pagina}: "
            f"{registros_pagina} registros extraidos"
        )

with open(salida, "w", encoding="utf-8") as archivo_json:

    json.dump(
        registros,
        archivo_json,
        ensure_ascii=False,
        indent=4
    )

print()
print("--------------------------------")
print("TOTAL GUARDADO:", len(registros))
print("--------------------------------")
print("Archivo creado:")
print(salida)