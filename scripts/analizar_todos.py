import json
import re
from pathlib import Path
from collections import Counter

carpeta_datos = Path(r"C:\Users\Admin\Desktop\ProyectoIA\datos")

# Buscamos únicamente los JSON brutos generados por extraer_todos.py
archivos = sorted(carpeta_datos.glob("VIG_fed_*__bruto.json"))

niveles_validos = {
    "LICENCIATURA",
    "MAESTRÍA",
    "DOCTORADO",
    "ESPECIALIDAD",
    "PROFESIONAL ASOCIADO",
    "TÉCNICO SUPERIOR UNIVERSITARIO"
}

modalidades_validas = {
    "ESCOLARIZADA",
    "MIXTA",
    "NO ESCOLARIZADA"
}

registros = []

print("========================================")
print("CARGANDO ARCHIVOS")
print("========================================")

for archivo in archivos:

    with open(archivo, "r", encoding="utf-8") as f:
        datos = json.load(f)

    registros.extend(datos)

    print(f"{archivo.name}: {len(datos)} registros")

print()
print(f"Archivos analizados: {len(archivos)}")
print(f"Registros cargados: {len(registros)}")


def limpiar_saltos(valor):
    if valor is None:
        return ""

    return " ".join(valor.replace("\n", " ").split())


def es_rvoe_fecha_valido(valor):
    valor = limpiar_saltos(valor)

    if not valor:
        return False

    patron = r"^[^/]+/\d{4}-\d{2}-\d{2}$"

    return bool(re.match(patron, valor))


estados = Counter()
niveles = Counter()
modalidades = Counter()

total_cdmx = 0
total_lic_cdmx = 0

sospechosos_nacionales = []
sospechosos_cdmx = []
sospechosos_lic_cdmx = []

rvoe_fecha_sospechosos = []

claves_registros = Counter()

for registro in registros:

    institucion = limpiar_saltos(registro.get("institucion"))
    estado = limpiar_saltos(registro.get("estado"))
    nivel = limpiar_saltos(registro.get("nivel_estudios"))
    programa = limpiar_saltos(registro.get("programa"))
    modalidad = limpiar_saltos(registro.get("modalidad"))
    rvoe_fecha = limpiar_saltos(registro.get("acuerdo_rvoe_fecha"))

    estados[estado] += 1
    niveles[nivel] += 1
    modalidades[modalidad] += 1

    es_cdmx = estado == "CIUDAD DE MÉXICO"
    es_licenciatura = nivel == "LICENCIATURA"

    if es_cdmx:
        total_cdmx += 1

    if es_cdmx and es_licenciatura:
        total_lic_cdmx += 1

    razones = []

    if not institucion:
        razones.append("institucion vacia")

    if not estado:
        razones.append("estado vacio")

    if not nivel:
        razones.append("nivel vacio")
    elif nivel not in niveles_validos:
        razones.append(f"nivel no reconocido: {nivel}")

    if not programa:
        razones.append("programa vacio")

    if not modalidad:
        razones.append("modalidad vacia")
    elif modalidad not in modalidades_validas:
        razones.append(f"modalidad no reconocida: {modalidad}")

    if not es_rvoe_fecha_valido(rvoe_fecha):
        razones.append(f"RVOE/fecha sospechoso: {rvoe_fecha}")

        rvoe_fecha_sospechosos.append({
            "fuente": registro.get("fuente"),
            "pagina": registro.get("pagina"),
            "institucion": institucion,
            "estado": estado,
            "nivel": nivel,
            "programa": programa,
            "rvoe_fecha": rvoe_fecha
        })

    if razones:

        caso = {
            "fuente": registro.get("fuente"),
            "pagina": registro.get("pagina"),
            "institucion": institucion,
            "estado": estado,
            "nivel": nivel,
            "programa": programa,
            "modalidad": modalidad,
            "rvoe_fecha": rvoe_fecha,
            "razones": razones
        }

        sospechosos_nacionales.append(caso)

        if es_cdmx:
            sospechosos_cdmx.append(caso)

        if es_cdmx and es_licenciatura:
            sospechosos_lic_cdmx.append(caso)

    # Clave provisional para buscar registros exactamente repetidos
    clave = (
        institucion,
        estado,
        nivel,
        programa,
        modalidad,
        rvoe_fecha
    )

    claves_registros[clave] += 1


duplicados = {
    clave: cantidad
    for clave, cantidad in claves_registros.items()
    if cantidad > 1
}

total_filas_duplicadas = sum(
    cantidad - 1
    for cantidad in duplicados.values()
)


print()
print("========================================")
print("RESUMEN GENERAL")
print("========================================")

print(f"Total de registros:             {len(registros)}")
print(f"Registros CDMX:                 {total_cdmx}")
print(f"Licenciaturas CDMX:             {total_lic_cdmx}")
print(f"Sospechosos nacionales:         {len(sospechosos_nacionales)}")
print(f"Sospechosos CDMX:               {len(sospechosos_cdmx)}")
print(f"Sospechosos Licenciatura CDMX:  {len(sospechosos_lic_cdmx)}")
print(f"RVOE/fecha sospechosos:          {len(rvoe_fecha_sospechosos)}")
print(f"Claves duplicadas:              {len(duplicados)}")
print(f"Filas duplicadas adicionales:   {total_filas_duplicadas}")


print()
print("========================================")
print("NIVELES ENCONTRADOS")
print("========================================")

for nivel, cantidad in niveles.most_common():
    print(f"{nivel}: {cantidad}")


print()
print("========================================")
print("MODALIDADES ENCONTRADAS")
print("========================================")

for modalidad, cantidad in modalidades.most_common():
    print(f"{modalidad}: {cantidad}")


print()
print("========================================")
print("SOSPECHOSOS LICENCIATURA CDMX")
print("========================================")

if not sospechosos_lic_cdmx:

    print("No se encontraron casos sospechosos.")

else:

    for i, caso in enumerate(sospechosos_lic_cdmx, start=1):

        print()
        print("----------------------------------------")
        print(f"CASO {i}")
        print("----------------------------------------")
        print("Fuente:", caso["fuente"])
        print("Pagina:", caso["pagina"])
        print("Institucion:", caso["institucion"])
        print("Estado:", caso["estado"])
        print("Nivel:", caso["nivel"])
        print("Programa:", caso["programa"])
        print("Modalidad:", caso["modalidad"])
        print("RVOE/fecha:", caso["rvoe_fecha"])
        print("Problema:", ", ".join(caso["razones"]))


# Guardamos los casos prioritarios para revisarlos posteriormente
archivo_revision = carpeta_datos / "revision_manual_licenciaturas_cdmx.json"

with open(archivo_revision, "w", encoding="utf-8") as f:

    json.dump(
        sospechosos_lic_cdmx,
        f,
        ensure_ascii=False,
        indent=4
    )


print()
print("========================================")
print("ARCHIVO DE REVISION")
print("========================================")
print(archivo_revision)

# ---------------------------------------------------------
# Crear archivo con TODOS los registros sospechosos de CDMX
# ---------------------------------------------------------

archivo_revision_cdmx = carpeta_datos / "revision_manual_cdmx.json"

with open(archivo_revision_cdmx, "w", encoding="utf-8") as f:
    json.dump(
        sospechosos_cdmx,
        f,
        ensure_ascii=False,
        indent=4
    )

print()
print("========================================")
print("REVISION COMPLETA CDMX")
print("========================================")
print(f"Registros sospechosos CDMX: {len(sospechosos_cdmx)}")
print("Archivo:")
print(archivo_revision_cdmx)

print()
print("========================================")
print("LISTA DE SOSPECHOSOS CDMX")
print("========================================")

for i, caso in enumerate(sospechosos_cdmx, start=1):

    print()
    print("----------------------------------------")
    print(f"CASO CDMX {i}")
    print("----------------------------------------")
    print("Fuente:", caso["fuente"])
    print("Pagina:", caso["pagina"])
    print("Institucion:", caso["institucion"])
    print("Nivel:", caso["nivel"])
    print("Programa:", caso["programa"])
    print("Modalidad:", caso["modalidad"])
    print("RVOE/fecha:", caso["rvoe_fecha"])
    print("Problema:", ", ".join(caso["razones"]))