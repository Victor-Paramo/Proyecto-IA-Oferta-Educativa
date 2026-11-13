import json
import re
from pathlib import Path
from collections import Counter

carpeta_datos = Path(r"C:\Users\Admin\Desktop\ProyectoIA\datos")

archivos = sorted(carpeta_datos.glob("VIG_fed_*__bruto.json"))

niveles_validos = [
    "LICENCIATURA",
    "MAESTRÍA",
    "DOCTORADO",
    "ESPECIALIDAD",
    "PROFESIONAL ASOCIADO",
    "TÉCNICO SUPERIOR UNIVERSITARIO"
]

registros_limpios = []

total_original = 0
registros_modificados = 0

cambios_nivel = Counter()
cambios_programa = 0


def normalizar_espacios(texto):
    if texto is None:
        return ""

    texto = texto.replace("\n", " ")
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def limpiar_nivel(nivel):
    """
    Corrige niveles contaminados por la leyenda
    'Información actualizada al 30 de abril de 2021'.

    Las variantes incluidas aquí fueron identificadas
    previamente durante la auditoría de los datos.
    """

    original = normalizar_espacios(nivel)
    mayusculas = original.upper()

    # Casos normales o contaminación sencilla
    for nivel_valido in niveles_validos:
        if mayusculas.startswith(nivel_valido):
            return nivel_valido

    # Variantes fuertemente contaminadas detectadas
    # durante la extracción de los PDF.
    equivalencias = {
        "LICInENfoCrIAmTaURcAión a": "LICENCIATURA",
        "IMnAfoESrmTRaÍAción a": "MAESTRÍA",
        "ESIPnEfCoIrAmLIDaAcDión a": "ESPECIALIDAD",
        "TÉCNICO SUPERIOR UNIInVEfoRrSmITAaRcIiOón a":
            "TÉCNICO SUPERIOR UNIVERSITARIO"
    }

    if original in equivalencias:
        return equivalencias[original]

    return original


def limpiar_programa(programa):
    """
    Elimina únicamente fragmentos conocidos de la leyenda
    'Información actualizada al 30 de abril de 2021'.
    """

    texto = normalizar_espacios(programa)

    patrones = [
        r"\s+ctualizada\s+al\s+30\s+de\s+abril\s+de\s+2021.*$",
        r"\s+actualizada\s+al\s+30\s+de\s+abril\s+de\s+2021.*$",
        r"\s+Información\s+actualizada\s+al\s+30\s+de\s+abril\s+de\s+2021.*$",
    ]

    for patron in patrones:
        texto = re.sub(
            patron,
            "",
            texto,
            flags=re.IGNORECASE
        )

    return texto.strip()


print("========================================")
print("LIMPIEZA DE DATOS")
print("========================================")

for archivo in archivos:

    print()
    print(f"Procesando: {archivo.name}")

    with open(archivo, "r", encoding="utf-8") as f:
        datos = json.load(f)

    total_original += len(datos)

    for registro in datos:

        # Conservamos una copia de los datos extraídos originalmente.
        nuevo = registro.copy()

        nivel_original = normalizar_espacios(
            registro.get("nivel_estudios")
        )

        programa_original = normalizar_espacios(
            registro.get("programa")
        )

        nivel_limpio = limpiar_nivel(nivel_original)
        programa_limpio = limpiar_programa(programa_original)

        modificado = False

        if nivel_limpio != nivel_original:
            cambios_nivel[(nivel_original, nivel_limpio)] += 1
            modificado = True

        if programa_limpio != programa_original:
            cambios_programa += 1
            modificado = True

        # Normalizamos solamente saltos de línea y espacios.
        nuevo["institucion"] = normalizar_espacios(
            registro.get("institucion")
        )

        nuevo["estado"] = normalizar_espacios(
            registro.get("estado")
        )

        nuevo["nivel_estudios"] = nivel_limpio

        nuevo["programa"] = programa_limpio

        nuevo["modalidad"] = normalizar_espacios(
            registro.get("modalidad")
        )

        # MUY IMPORTANTE:
        # RVOE/fecha se conserva exactamente en contenido.
        nuevo["acuerdo_rvoe_fecha"] = normalizar_espacios(
            registro.get("acuerdo_rvoe_fecha")
        )

        if modificado:
            registros_modificados += 1

        registros_limpios.append(nuevo)

    print(f"Registros procesados: {len(datos)}")


archivo_salida = carpeta_datos / "oferta_educativa_limpia.json"

with open(archivo_salida, "w", encoding="utf-8") as f:
    json.dump(
        registros_limpios,
        f,
        ensure_ascii=False,
        indent=4
    )


print()
print("========================================")
print("RESULTADO")
print("========================================")

print(f"Registros originales:     {total_original}")
print(f"Registros guardados:      {len(registros_limpios)}")
print(f"Registros modificados:    {registros_modificados}")
print(f"Programas corregidos:     {cambios_programa}")

print()
print("========================================")
print("CAMBIOS DE NIVEL")
print("========================================")

if not cambios_nivel:

    print("No se realizaron cambios de nivel.")

else:

    for (original, limpio), cantidad in cambios_nivel.items():

        print()
        print(f"Cantidad: {cantidad}")
        print(f"ANTES:   {original}")
        print(f"DESPUES: {limpio}")


print()
print("========================================")
print("ARCHIVO CREADO")
print("========================================")
print(archivo_salida)