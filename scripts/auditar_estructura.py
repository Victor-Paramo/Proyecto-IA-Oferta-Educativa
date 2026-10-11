
import json
import re
from pathlib import Path
from collections import defaultdict, Counter

carpeta = Path(r"C:\Users\Admin\Desktop\ProyectoIA\datos")
archivo = carpeta / "oferta_educativa_limpia.json"

with open(archivo, "r", encoding="utf-8") as f:
    registros = json.load(f)


def limpiar(valor):
    if valor is None:
        return ""
    return " ".join(str(valor).split()).strip()


def obtener(registro, campo):
    return limpiar(registro.get(campo, ""))


def analizar_dependencia(datos, determinantes, dependiente):
    grupos = defaultdict(set)

    for r in datos:
        clave = tuple(obtener(r, c) for c in determinantes)
        valor = obtener(r, dependiente)

        if all(clave) and valor:
            grupos[clave].add(valor)

    conflictos = {
        k: sorted(v)
        for k, v in grupos.items()
        if len(v) > 1
    }

    return len(grupos), conflictos


def mostrar_dependencia(titulo, datos, campos, destino):
    total, conflictos = analizar_dependencia(
        datos, campos, destino
    )

    print()
    print("-" * 55)
    print(titulo)
    print("-" * 55)
    print("Grupos analizados:", total)
    print("Grupos con varios valores:", len(conflictos))

    for clave, valores in list(conflictos.items())[:5]:
        print("Clave:", clave)
        print("Valores:", valores)

    return {
        "determinantes": campos,
        "dependiente": destino,
        "grupos_analizados": total,
        "grupos_conflictivos": len(conflictos),
        "ejemplos": [
            {"clave": list(k), "valores": v}
            for k, v in list(conflictos.items())[:20]
        ]
    }


def obtener_rvoe(registro):
    texto = obtener(registro, "acuerdo_rvoe_fecha")
    return re.split(r"/", texto, maxsplit=1)[0].strip()


cdmx = [
    r for r in registros
    if obtener(r, "estado") == "CIUDAD DE MÉXICO"
]

licenciaturas = [
    r for r in cdmx
    if obtener(r, "nivel_estudios") == "LICENCIATURA"
]

print("=" * 55)
print("AUDITORIA DE ESTRUCTURA")
print("=" * 55)

print("Registros nacionales:", len(registros))
print("Registros CDMX:", len(cdmx))
print("Licenciaturas CDMX:", len(licenciaturas))

print()
print("=" * 55)
print("DIVERSIDAD DE ATRIBUTOS - LICENCIATURAS CDMX")
print("=" * 55)

campos = [
    "institucion",
    "estado",
    "nivel_estudios",
    "programa",
    "modalidad",
    "acuerdo_rvoe_fecha"
]

for campo in campos:
    valores = {
        obtener(r, campo)
        for r in licenciaturas
        if obtener(r, campo)
    }
    print(f"{campo}: {len(valores)} valores distintos")


print()
print("=" * 55)
print("DEPENDENCIAS FUNCIONALES CANDIDATAS")
print("=" * 55)

resultados = []

pruebas = [
    (
        "PROGRAMA -> NIVEL",
        ["programa"],
        "nivel_estudios",
        cdmx
    ),
    (
        "INSTITUCION -> PROGRAMA",
        ["institucion"],
        "programa",
        licenciaturas
    ),
    (
        "INSTITUCION + PROGRAMA -> MODALIDAD",
        ["institucion", "programa"],
        "modalidad",
        licenciaturas
    ),
    (
        "INSTITUCION + PROGRAMA + MODALIDAD -> RVOE",
        ["institucion", "programa", "modalidad"],
        "acuerdo_rvoe_fecha",
        licenciaturas
    ),
    (
        "INSTITUCION -> ESTADO (NACIONAL)",
        ["institucion"],
        "estado",
        registros
    )
]

for titulo, determinantes, dependiente, datos in pruebas:
    resultado = mostrar_dependencia(
        titulo, datos, determinantes, dependiente
    )
    resultado["prueba"] = titulo
    resultados.append(resultado)


print()
print("=" * 55)
print("ANALISIS DE RVOE - LICENCIATURAS CDMX")
print("=" * 55)

rvoes = defaultdict(list)

for r in licenciaturas:
    numero = obtener_rvoe(r)

    if numero:
        rvoes[numero].append(r)

repetidos = {
    numero: filas
    for numero, filas in rvoes.items()
    if len(filas) > 1
}

print("RVOE distintos:", len(rvoes))
print("RVOE repetidos:", len(repetidos))

for numero, filas in list(repetidos.items())[:10]:
    print()
    print("RVOE:", numero)
    print("Apariciones:", len(filas))

    for r in filas[:3]:
        print(
            obtener(r, "institucion"),
            "|",
            obtener(r, "programa"),
            "|",
            obtener(r, "modalidad")
        )


print()
print("=" * 55)
print("REGISTROS EXACTAMENTE REPETIDOS")
print("=" * 55)

claves = Counter(
    tuple(obtener(r, campo) for campo in campos)
    for r in licenciaturas
)

duplicados = {
    k: n for k, n in claves.items() if n > 1
}

adicionales = sum(n - 1 for n in duplicados.values())

print("Grupos repetidos:", len(duplicados))
print("Filas adicionales repetidas:", adicionales)


reporte = {
    "total_nacional": len(registros),
    "total_cdmx": len(cdmx),
    "licenciaturas_cdmx": len(licenciaturas),
    "dependencias": resultados,
    "rvoe_distintos": len(rvoes),
    "rvoe_repetidos": len(repetidos),
    "grupos_duplicados": len(duplicados),
    "filas_duplicadas_adicionales": adicionales
}

salida = carpeta / "auditoria_estructura.json"

with open(salida, "w", encoding="utf-8") as f:
    json.dump(
        reporte,
        f,
        ensure_ascii=False,
        indent=4
    )

print()
print("=" * 55)
print("ARCHIVO DE AUDITORIA CREADO")
print("=" * 55)
print(salida)
