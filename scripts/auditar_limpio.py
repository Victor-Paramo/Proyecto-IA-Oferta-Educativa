import json
from pathlib import Path
from collections import Counter

archivo = Path(
    r"C:\Users\Admin\Desktop\ProyectoIA\datos\oferta_educativa_limpia.json"
)

niveles_validos = {
    "LICENCIATURA",
    "MAESTRÍA",
    "DOCTORADO",
    "ESPECIALIDAD",
    "PROFESIONAL ASOCIADO",
    "TÉCNICO SUPERIOR UNIVERSITARIO"
}

with open(archivo, "r", encoding="utf-8") as f:
    registros = json.load(f)

niveles = Counter()
estados = Counter()

sospechosos_nivel = []
sospechosos_nivel_cdmx = []

licenciaturas_cdmx = 0

for registro in registros:

    nivel = registro.get("nivel_estudios", "").strip()
    estado = registro.get("estado", "").strip()

    niveles[nivel] += 1
    estados[estado] += 1

    if estado == "CIUDAD DE MÉXICO" and nivel == "LICENCIATURA":
        licenciaturas_cdmx += 1

    if nivel not in niveles_validos:

        caso = {
            "fuente": registro.get("fuente"),
            "pagina": registro.get("pagina"),
            "institucion": registro.get("institucion"),
            "estado": estado,
            "nivel": nivel,
            "programa": registro.get("programa"),
            "modalidad": registro.get("modalidad"),
            "acuerdo_rvoe_fecha": registro.get("acuerdo_rvoe_fecha")
        }

        sospechosos_nivel.append(caso)

        if estado == "CIUDAD DE MÉXICO":
            sospechosos_nivel_cdmx.append(caso)


print("========================================")
print("AUDITORIA DEL JSON LIMPIO")
print("========================================")

print(f"Total de registros:             {len(registros)}")
print(f"Registros CDMX:                 {estados['CIUDAD DE MÉXICO']}")
print(f"Licenciaturas CDMX:             {licenciaturas_cdmx}")
print(f"Niveles no reconocidos:         {len(sospechosos_nivel)}")
print(f"Niveles no reconocidos CDMX:    {len(sospechosos_nivel_cdmx)}")

print()
print("========================================")
print("NIVELES DESPUES DE LA LIMPIEZA")
print("========================================")

for nivel, cantidad in niveles.most_common():
    marca = ""

    if nivel not in niveles_validos:
        marca = "  <-- REVISAR"

    print(f"{nivel}: {cantidad}{marca}")

print()
print("========================================")
print("NO RECONOCIDOS EN CDMX")
print("========================================")

if not sospechosos_nivel_cdmx:
    print("Ninguno.")

else:
    for i, caso in enumerate(sospechosos_nivel_cdmx, start=1):

        print()
        print(f"CASO {i}")
        print("Fuente:", caso["fuente"])
        print("Pagina:", caso["pagina"])
        print("Institucion:", caso["institucion"])
        print("Nivel:", caso["nivel"])
        print("Programa:", caso["programa"])
        print("Modalidad:", caso["modalidad"])
        print("RVOE/fecha:", caso["acuerdo_rvoe_fecha"])