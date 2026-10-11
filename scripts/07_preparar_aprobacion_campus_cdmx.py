"""Prepara la revision humana de planteles explicitos de licenciaturas CDMX.

Entrada: datos/revision_instituciones_planteles_cdmx.csv
Salida:  datos/aprobacion_campus_explicitos_cdmx.csv
No accede a PostgreSQL ni aprueba/fusiona entidades automaticamente.
"""
import csv
import re
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / 'datos' / 'revision_instituciones_planteles_cdmx.csv'
SALIDA = RAIZ / 'datos' / 'aprobacion_campus_explicitos_cdmx.csv'
CAMPOS = [
    'nombre_en_pdf', 'registros', 'institucion_propuesta', 'plantel_propuesto',
    'alertas', 'institucion_aprobada', 'plantel_aprobado',
    'decision_manual', 'observaciones',
]


def limpia(valor):
    return ' '.join((valor or '').split()).strip()


def alertas(nombre, institucion, plantel):
    avisos = []
    if not institucion or not plantel:
        avisos.append('FALTA_INSTITUCION_O_PLANTEL')
    if '(' in nombre or ')' in nombre or '(' in plantel or ')' in plantel:
        avisos.append('PARENTESIS_REVISAR')
    if re.search(r'(?i)\b(CAMPUS|PLANTEL|SEDE|UNIDAD)\s*$', nombre):
        avisos.append('NOMBRE_TRUNCADO')
    if re.search(r'(?i)(TECVN|PCLEAN|CEPNLT|REOC|EPSETCU|CL EAN)', nombre):
        avisos.append('POSIBLE_ERROR_EXTRACCION')
    return avisos


def main():
    if not ENTRADA.is_file():
        sys.exit(f'No se encontro el CSV de entrada: {ENTRADA}')
    if SALIDA.exists():
        sys.exit(f'El archivo de salida ya existe; no se sobrescribio: {SALIDA}')
    with ENTRADA.open('r', encoding='utf-8-sig', newline='') as f:
        lector = csv.DictReader(f)
        requeridos = {'nombre_en_pdf', 'registros', 'prioridad_revision',
                      'institucion_propuesta', 'plantel_propuesto'}
        faltantes = requeridos - set(lector.fieldnames or [])
        if faltantes:
            sys.exit('Faltan columnas: ' + ', '.join(sorted(faltantes)))
        filas = list(lector)

    seleccionadas = [r for r in filas if limpia(r['prioridad_revision']) == '3_MEDIA']
    if len(seleccionadas) != 69:
        sys.exit(f'Se esperaban 69 denominaciones de prioridad media; hay {len(seleccionadas)}. Revisar archivo origen.')
    salida = []
    vistos = set()
    for r in seleccionadas:
        nombre = limpia(r['nombre_en_pdf'])
        if not nombre or nombre in vistos:
            sys.exit(f'Nombre vacio o duplicado: {nombre!r}')
        vistos.add(nombre)
        institucion = limpia(r['institucion_propuesta'])
        plantel = limpia(r['plantel_propuesto'])
        if not institucion or not plantel:
            sys.exit(f'Propuesta incompleta: {nombre!r}')
        salida.append({
            'nombre_en_pdf': nombre,
            'registros': int(r['registros']),
            'institucion_propuesta': institucion,
            'plantel_propuesto': plantel,
            'alertas': '; '.join(alertas(nombre, institucion, plantel)),
            'institucion_aprobada': '',
            'plantel_aprobado': '',
            'decision_manual': 'PENDIENTE',
            'observaciones': '',
        })
    salida.sort(key=lambda r: (r['institucion_propuesta'], r['plantel_propuesto'], r['nombre_en_pdf']))
    with SALIDA.open('w', encoding='utf-8-sig', newline='') as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS)
        escritor.writeheader()
        escritor.writerows(salida)

    print('ALCANCE: licenciaturas de Ciudad de Mexico (CDMX)')
    print(f'Denominaciones para revision: {len(salida)}')
    print(f'Registros representados: {sum(r["registros"] for r in salida):,}')
    print(f'Instituciones propuestas distintas: {len({r["institucion_propuesta"] for r in salida})}')
    print(f'Filas con alertas: {sum(bool(r["alertas"]) for r in salida)}')
    print(f'Archivo generado: {SALIDA}')
    print('No se ha aprobado ningun nombre; no hubo acceso a PostgreSQL.')
    print('Para cada fila, escribir APROBAR o RECHAZAR en decision_manual y completar las columnas aprobadas si corresponde.')


if __name__ == '__main__':
    main()
