import json
from collections import Counter

archivo = r"C:\Users\Admin\Desktop\ProyectoIA\datos\VIG_fed_A-C_bruto.json"

with open(archivo, "r", encoding="utf-8") as f:
    registros = json.load(f)

total = len(registros)

estados = Counter()
niveles = Counter()
modalidades = Counter()

registros_cdmx = 0
licenciaturas_cdmx = 0

sospechosos = []

# Valores que esperamos encontrar normalmente
niveles_validos = {
    "LICENCIATURA",
    "MAESTRÍA",
    "DOCTORADO",
    "ESPECIALIDAD"
}

modalidades_validas = {
    "ESCOLARIZADA",
    "MIXTA",
    "NO ESCOLARIZADA"
}

for registro in registros:

    # Solo para analizar correctamente los valores.
    # NO modifica el JSON original.
    estado = (registro.get("estado") or "").replace("\n", " ").strip()
    nivel = (registro.get("nivel_estudios") or "").replace("\n", " ").strip()
    modalidad = (registro.get("modalidad") or "").replace("\n", " ").strip()

    estados[estado] += 1
    niveles[nivel] += 1
    modalidades[modalidad] += 1

    # Nuestro alcance principal
    if estado == "CIUDAD DE MÉXICO":
        registros_cdmx += 1

        if nivel == "LICENCIATURA":
            licenciaturas_cdmx += 1

    # Detección básica de registros sospechosos
    razones = []

    if not registro.get("institucion"):
        razones.append("institucion vacia")

    if not estado:
        razones.append("estado vacio")

    if not registro.get("programa"):
        razones.append("programa vacio")

    if nivel not in niveles_validos:
        razones.append(f"nivel sospechoso: {nivel}")

    if modalidad not in modalidades_validas:
        razones.append(f"modalidad sospechosa: {modalidad}")

    if razones:
        sospechosos.append({
            "pagina": registro.get("pagina"),
            "institucion": registro.get("institucion"),
            "estado": estado,
            "nivel": nivel,
            "programa": registro.get("programa"),
            "modalidad": modalidad,
            "razones": razones
        })

print("\n========== RESUMEN ==========")
print(f"Total de registros:        {total}")
print(f"Registros de CDMX:         {registros_cdmx}")
print(f"Licenciaturas de CDMX:     {licenciaturas_cdmx}")
print(f"Registros sospechosos:     {len(sospechosos)}")

print("\n========== ESTADOS ==========")
for estado, cantidad in estados.most_common():
    print(f"{estado}: {cantidad}")

print("\n========== NIVELES ==========")
for nivel, cantidad in niveles.most_common():
    print(f"{nivel}: {cantidad}")

print("\n========== MODALIDADES ==========")
for modalidad, cantidad in modalidades.most_common():
    print(f"{modalidad}: {cantidad}")

print("\n========== SOSPECHOSOS ==========")

if not sospechosos:
    print("No se detectaron registros sospechosos.")
else:
    for registro in sospechosos:
        print("\n------------------------------")
        print("Pagina:", registro["pagina"])
        print("Institucion:", registro["institucion"])
        print("Estado:", registro["estado"])
        print("Nivel:", registro["nivel"])
        print("Programa:", registro["programa"])
        print("Modalidad:", registro["modalidad"])
        print("Problema:", ", ".join(registro["razones"]))