"""Prepara la revisión MANUAL de instituciones y planteles de licenciatura en CDMX.

Entrada: datos/correspondencias_instituciones_planteles_cdmx.csv
Salidas (sin sobreescribir):
  datos/revision_instituciones_planteles_cdmx.csv
  datos/grupos_instituciones_cdmx.csv
  datos/resumen_revision_instituciones_cdmx.txt

No se conecta a PostgreSQL, no aprueba casos y no modifica la entrada.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "datos"
ENTRADA = DATOS / "correspondencias_instituciones_planteles_cdmx.csv"
REVISION = DATOS / "revision_instituciones_planteles_cdmx.csv"
GRUPOS = DATOS / "grupos_instituciones_cdmx.csv"
RESUMEN = DATOS / "resumen_revision_instituciones_cdmx.txt"
TOTAL_ESPERADO = 2810  # Solo licenciaturas CDMX, NO los 27,054 nacionales.


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.upper())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^A-Z0-9 ]", " ", texto).split())


def analizar(fila: dict[str, str]) -> tuple[str, str, str, str]:
    """Devuelve prioridad, motivo adicional, institución candidata, sede candidata.

    Las candidatas nunca se consideran aprobadas.
    """
    original = fila["nombre_en_pdf"].strip()
    estado = fila["estado_revision"].strip().upper()
    motivo = fila["motivo"]
    inst = fila["institucion_propuesta"].strip()
    sede = fila["plantel_propuesto"].strip()
    n = normalizar(original)

    if ("contaminado" in motivo.lower() or "truncado" in motivo.lower()
            or "sin institución o sede completa" in motivo.lower()
            or not original or original.count("(") != original.count(")")):
        return "1_CRITICA", "Texto incompleto o sospechoso: contrastar con PDF", inst, sede
    if "PCLEAN" in n or "ACTUALIZADA" in n or "TE CUN" in n:
        return "1_CRITICA", "Posible interferencia de texto en la extracción", inst, sede
    if "(" in original or ")" in original:
        # Aunque parezca una sede, solo sugerirla para revisión humana.
        m = re.fullmatch(r"(.+?)\s*\(([^()]*)\)\s*", original)
        if m and not inst:
            inst, sede = m.group(1).strip(), m.group(2).strip()
        return "2_ALTA", "Paréntesis: verificar si identifica sede o forma parte del nombre", inst, sede
    if estado == "REVISAR":
        return "2_ALTA", "Clasificado REVISAR en diagnóstico previo", inst, sede
    if sede:
        return "3_MEDIA", "Campus explícito: verificar institución y nombre del plantel", inst, sede
    return "4_NORMAL", "Plantel no identificado: no inventar sede", inst, sede


def escribir_csv(ruta: Path, filas: list[dict[str, str]], columnas: list[str]) -> None:
    with ruta.open("x", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columnas, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)


def main() -> None:
    if not ENTRADA.is_file():
        raise SystemExit(f"No se encontró el archivo: {ENTRADA}")
    destinos = [REVISION, GRUPOS, RESUMEN]
    existentes = [str(p) for p in destinos if p.exists()]
    if existentes:
        raise SystemExit("No se sobrescriben revisiones previas. Archivos existentes:\n" + "\n".join(existentes))

    with ENTRADA.open(encoding="utf-8-sig", newline="") as f:
        lector = csv.DictReader(f)
        columnas_originales = lector.fieldnames or []
        necesarias = {
            "nombre_en_pdf", "registros", "institucion_propuesta", "plantel_propuesto",
            "estado_revision", "motivo", "institucion_aprobada", "plantel_aprobado",
            "decision_manual", "observaciones",
        }
        if not necesarias.issubset(columnas_originales):
            raise SystemExit("Faltan columnas: " + ", ".join(sorted(necesarias - set(columnas_originales))))
        base = list(lector)

    if len(base) != 330:
        raise SystemExit(f"Se esperaban 330 denominaciones de CDMX; encontradas: {len(base)}")
    try:
        total = sum(int(f["registros"]) for f in base)
    except ValueError as exc:
        raise SystemExit(f"Columna registros inválida: {exc}") from exc
    if total != TOTAL_ESPERADO:
        raise SystemExit(f"Total inconsistente: {total}; esperado {TOTAL_ESPERADO} licenciaturas CDMX")
    nombres = [f["nombre_en_pdf"] for f in base]
    if len(nombres) != len(set(nombres)):
        raise SystemExit("Hay nombres originales repetidos; se requiere revisar el CSV antes de continuar")

    filas = []
    grupos = defaultdict(list)
    for fila in base:
        prioridad, alerta, inst, sede = analizar(fila)
        nuevo = dict(fila)
        nuevo.update({
            "prioridad_revision": prioridad,
            "alerta_revision": alerta,
            "institucion_candidata_revision": inst,
            "plantel_candidato_revision": sede,
            "clave_agrupacion_sugerida": normalizar(inst) if inst else "",
        })
        filas.append(nuevo)
        if inst:
            grupos[normalizar(inst)].append(nuevo)

    # Las agrupaciones son solo para visualizar nombres semejantes; no son fusiones.
    filas.sort(key=lambda r: (r["prioridad_revision"], -int(r["registros"]), r["nombre_en_pdf"]))
    registros_grupo = []
    for clave, miembros in grupos.items():
        if len(miembros) < 2:
            continue
        registros_grupo.append({
            "clave_agrupacion_sugerida": clave,
            "denominaciones": str(len(miembros)),
            "registros_cdmx": str(sum(int(m["registros"]) for m in miembros)),
            "nombres_originales": " | ".join(sorted(m["nombre_en_pdf"] for m in miembros)),
            "advertencia": "Grupo sugerido; no implica misma persona jurídica ni aprobación",
        })
    registros_grupo.sort(key=lambda r: (-int(r["registros_cdmx"]), r["clave_agrupacion_sugerida"]))

    escribir_csv(REVISION, filas, columnas_originales + [
        "prioridad_revision", "alerta_revision", "institucion_candidata_revision",
        "plantel_candidato_revision", "clave_agrupacion_sugerida",
    ])
    escribir_csv(GRUPOS, registros_grupo, [
        "clave_agrupacion_sugerida", "denominaciones", "registros_cdmx",
        "nombres_originales", "advertencia",
    ])
    resumen = Counter(r["prioridad_revision"] for r in filas)
    texto = (
        "REVISIÓN DE INSTITUCIONES Y PLANTELES - LICENCIATURAS CDMX\n"
        f"Denominaciones: {len(filas)}\nRegistros CDMX representados: {total}\n"
        + "\n".join(f"{k}: {resumen[k]}" for k in sorted(resumen))
        + f"\nGrupos sugeridos con 2+ denominaciones: {len(registros_grupo)}\n"
        "\nIMPORTANTE: No se aprobó ni fusionó ninguna institución o plantel.\n"
        "Revisar los nombres frente a la fuente PDF antes de rellenar las columnas\n"
        "institucion_aprobada, plantel_aprobado y decision_manual.\n"
        "La ausencia de plantel explícito no autoriza inventarlo.\n"
        "No hay conexión ni modificaciones a PostgreSQL.\n"
    )
    RESUMEN.write_text(texto, encoding="utf-8")
    print(texto)
    print(f"CSV para revisión manual: {REVISION}")
    print(f"Grupos sugeridos: {GRUPOS}")
    print(f"Resumen: {RESUMEN}")


if __name__ == "__main__":
    main()
