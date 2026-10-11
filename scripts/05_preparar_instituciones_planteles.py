"""Genera propuestas auditables de institucion/plantel para CDMX.

Entrada: datos/diagnostico_instituciones_cdmx.csv
Salida: datos/correspondencias_instituciones_planteles_cdmx.csv
No se conecta a PostgreSQL ni modifica archivos existentes.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ENTRADA = RAIZ / 'datos' / 'diagnostico_instituciones_cdmx.csv'
SALIDA = RAIZ / 'datos' / 'correspondencias_instituciones_planteles_cdmx.csv'

# Se usan solo indicadores explícitos y un nombre de plantel presente.
# Los paréntesis se dejan para revisión, no se separan automáticamente.
MARCADOR = re.compile(r'\s*,?\s*\b(CAMPUS|PLANTEL|SEDE|UNIDAD|EXTENSI[ÓO]N)\b\s*[:,.-]?\s*', re.I)
SOSPECHOSOS = ('PCLEAN', 'CEPNL', 'CENT(REO', 'TECVN', 'TE(CUN', 'EOSTRU', 'EPSET', 'PLARNOT', 'INFORMACI', 'ACTUALIZADA')


def clave_nombre(texto: str) -> str:
    """Clave auxiliar para detectar diferencias menores; no fusiona entidades."""
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r'[^A-Z0-9 ]', ' ', texto.upper())
    return ' '.join(texto.split())


def clasificar(nombre: str):
    nombre = ' '.join(nombre.split())
    if not nombre:
        return '', '', 'REVISAR', 'Nombre original vacío'
    if any(k in clave_nombre(nombre) for k in SOSPECHOSOS) or (nombre.count('(') != nombre.count(')')):
        return '', '', 'REVISAR', 'Nombre posiblemente contaminado, truncado o con paréntesis incompletos'
    coincidencias = list(MARCADOR.finditer(nombre))
    if coincidencias:
        m = coincidencias[0]
        base = nombre[:m.start()].strip(' ,.-')
        plantel = nombre[m.end():].strip(' ,.-')
        if not base or not plantel:
            return '', '', 'REVISAR', 'Indicador de plantel sin institución o sede completa'
        if len(coincidencias) > 1:
            return base, plantel, 'REVISAR', 'Múltiples indicadores; comprobar límites del nombre'
        if '(' in plantel or ')' in plantel:
            return base, plantel, 'REVISAR', 'Campus explícito con calificativo entre paréntesis; comprobar sede'
        return base, plantel, 'PROPUESTA', 'Separación por indicador explícito; pendiente de aprobación humana'
    if '(' in nombre or ')' in nombre:
        return '', '', 'REVISAR', 'Posible sede entre paréntesis; no se separa automáticamente'
    return nombre, '', 'PROPUESTA', 'Sin indicador explícito; institución propuesta, plantel desconocido'


def main():
    if not ENTRADA.is_file():
        raise SystemExit(f'No se encontró el archivo: {ENTRADA}')
    with ENTRADA.open('r', encoding='utf-8-sig', newline='') as f:
        lector = csv.DictReader(f)
        requeridas = {'nombre_en_pdf', 'registros', 'programas_distintos', 'modalidades_distintas'}
        if not requeridas.issubset(set(lector.fieldnames or [])):
            raise SystemExit(f'Columnas necesarias: {sorted(requeridas)}')
        originales = list(lector)
    filas = []
    for r in originales:
        nombre = r['nombre_en_pdf'].strip()
        institucion, plantel, estado, motivo = clasificar(nombre)
        filas.append({
            'nombre_en_pdf': nombre,
            'registros': r['registros'],
            'programas_distintos': r['programas_distintos'],
            'modalidades_distintas': r['modalidades_distintas'],
            'institucion_propuesta': institucion,
            'plantel_propuesto': plantel,
            'clave_institucion_auxiliar': clave_nombre(institucion) if institucion else '',
            'estado_revision': estado,
            'motivo': motivo,
            'institucion_aprobada': '',
            'plantel_aprobado': '',
            'decision_manual': '',
            'observaciones': '',
        })

    # Solo advertencia; jamás fusionamos automáticamente variantes.
    grupos = defaultdict(list)
    for fila in filas:
        if fila['clave_institucion_auxiliar']:
            grupos[fila['clave_institucion_auxiliar']].append(fila)
    variantes = 0
    for miembros in grupos.values():
        nombres = {f['institucion_propuesta'] for f in miembros}
        if len(nombres) > 1:
            variantes += 1
            for f in miembros:
                f['estado_revision'] = 'REVISAR'
                f['motivo'] += '; posible variante ortográfica de institución'

    if SALIDA.exists():
        raise SystemExit(f'El archivo de salida ya existe. Se dejó intacto: {SALIDA}')
    with SALIDA.open('w', encoding='utf-8-sig', newline='') as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)

    conteos = Counter(f['estado_revision'] for f in filas)
    n_registros = sum(int(f['registros']) for f in filas)
    print(f'Nombres examinados: {len(filas)}')
    print(f'Registros que representan: {n_registros:,}')
    print(f'Propuestas por revisar/aprobar: {conteos["PROPUESTA"]}')
    print(f'Casos que requieren revisión especial: {conteos["REVISAR"]}')
    print(f'Grupos de posibles variantes ortográficas: {variantes}')
    print(f'CSV generado: {SALIDA}')
    print('Ninguna tabla de PostgreSQL fue modificada.')
    print('No se ha aprobado ni fusionado automáticamente ninguna institución.')


if __name__ == '__main__':
    main()
