"""Carga SOLO correspondencias aprobadas de licenciaturas de CDMX.

Uso (desde la raiz ProyectoIA):
    python scripts/08_cargar_campus_aprobados_cdmx.py          # simulacion
    python scripts/08_cargar_campus_aprobados_cdmx.py --apply  # aplica carga

Entrada: datos/aprobacion_campus_explicitos_cdmx.csv
No carga ofertas ni modifica los registros de origen.
Requiere psycopg2 y PostgreSQL con las tablas del modelo relacional.
"""
import argparse
import csv
import getpass
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / 'datos' / 'aprobacion_campus_explicitos_cdmx.csv'


def limpio(x):
    return ' '.join((x or '').split()).strip()


def leer():
    with CSV.open('r', encoding='utf-8-sig', newline='') as f:
        filas = list(csv.DictReader(f))
    if len(filas) != 69:
        raise ValueError(f'Se esperaban 69 denominaciones; hay {len(filas)}')
    nombres = [limpio(f['nombre_en_pdf']) for f in filas]
    if len(set(nombres)) != len(nombres):
        raise ValueError('Hay nombres PDF duplicados')
    validos = {'APROBAR', 'PENDIENTE', 'RECHAZAR'}
    aprobados = []
    for f in filas:
        d = limpio(f['decision_manual']).upper()
        if d not in validos:
            raise ValueError(f'Decision invalida {d!r} en {f["nombre_en_pdf"]}')
        if d != 'APROBAR':
            continue
        institucion = limpio(f['institucion_aprobada'])
        plantel = limpio(f['plantel_aprobado'])
        if not institucion or not plantel:
            raise ValueError(f'Aprobacion incompleta: {f["nombre_en_pdf"]}')
        # Evitar aprobar una version distinta sin trazabilidad documental.
        if institucion != limpio(f['institucion_propuesta']) or plantel != limpio(f['plantel_propuesto']):
            raise ValueError(f'La propuesta fue modificada; revisar antes de cargar: {f["nombre_en_pdf"]}')
        aprobados.append((limpio(f['nombre_en_pdf']), institucion, plantel))
    return filas, aprobados


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Insertar aprobados en PostgreSQL')
    args = parser.parse_args()
    if not CSV.is_file():
        sys.exit(f'Falta el CSV: {CSV}')
    filas, aprobados = leer()
    print('Alcance: SOLO licenciaturas de CDMX')
    print(f'Filas del CSV: {len(filas)}')
    print('Decisiones:', dict(Counter(limpio(f['decision_manual']).upper() for f in filas)))
    print(f'Correspondencias aprobadas: {len(aprobados)}')
    print(f'Instituciones candidatas aprobadas: {len(set(x[1] for x in aprobados))}')
    if not args.apply:
        print('SIMULACION. No se ha modificado PostgreSQL.')
        print('Para insertar únicamente las filas APROBAR: usar --apply.')
        return
    if not aprobados:
        sys.exit('No hay filas aprobadas. No se hace ninguna carga.')

    import psycopg2
    contrasena = getpass.getpass('Contrasena PostgreSQL (postgres): ')
    cnx = psycopg2.connect(host='localhost', port=5432, dbname='oferta_educativa',
                           user='postgres', password=contrasena)
    try:
        with cnx:
            with cnx.cursor() as cur:
                cur.execute('SELECT id_estado FROM catalogo.estado WHERE nombre = %s',
                            ('CIUDAD DE MÉXICO',))
                estado = cur.fetchone()
                if estado is None:
                    raise RuntimeError('No existe CIUDAD DE MÉXICO en catalogo.estado')
                id_estado = estado[0]
                cur.execute('SELECT nombre, id_institucion FROM catalogo.institucion')
                inst_por_nombre = {}
                for nombre, ident in cur.fetchall():
                    inst_por_nombre.setdefault(nombre, []).append(ident)
                instituciones_nuevas = planteles_nuevos = 0
                parejas = sorted(set((i, p) for _, i, p in aprobados))
                for institucion, plantel in parejas:
                    identidades = inst_por_nombre.get(institucion, [])
                    if len(identidades) > 1:
                        raise RuntimeError(f'Institucion duplicada en base: {institucion}')
                    if identidades:
                        id_institucion = identidades[0]
                    else:
                        cur.execute('INSERT INTO catalogo.institucion(nombre) VALUES (%s) RETURNING id_institucion',
                                    (institucion,))
                        id_institucion = cur.fetchone()[0]
                        inst_por_nombre[institucion] = [id_institucion]
                        instituciones_nuevas += 1
                    cur.execute('''SELECT id_plantel FROM catalogo.plantel
                                   WHERE id_institucion = %s AND id_estado = %s AND nombre = %s''',
                                (id_institucion, id_estado, plantel))
                    coincidentes = cur.fetchall()
                    if len(coincidentes) > 1:
                        raise RuntimeError(f'Plantel duplicado en base: {institucion} / {plantel}')
                    if not coincidentes:
                        cur.execute('''INSERT INTO catalogo.plantel(id_institucion,id_estado,nombre)
                                       VALUES (%s,%s,%s)''', (id_institucion, id_estado, plantel))
                        planteles_nuevos += 1
                # No cambiamos vinculos, ofertas ni otras entidades en esta fase.
                print(f'Instituciones nuevas: {instituciones_nuevas}')
                print(f'Planteles nuevos: {planteles_nuevos}')
                print(f'Parejas institucion/plantel aprobadas procesadas: {len(parejas)}')
        print('Transaccion confirmada.')
    finally:
        cnx.close()


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError) as e:
        sys.exit(f'ERROR: {e}')
