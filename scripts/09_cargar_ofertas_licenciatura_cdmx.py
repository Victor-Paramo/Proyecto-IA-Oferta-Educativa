"""Carga integral provisional de licenciaturas CDMX.

Fuente: origen.registro_origen (ya cargado). Reutiliza correspondencias
APROBAR del CSV existente, sin inventar planteles para las demás.

Uso desde ProyectoIA:
  python scripts/09_cargar_ofertas_licenciatura_cdmx.py
  python scripts/09_cargar_ofertas_licenciatura_cdmx.py --apply

En la primera ejecución solo lee PostgreSQL y simula. --apply inserta
las ofertas, autorizaciones y vínculos dentro de una única transacción.
No modifica, borra ni reemplaza registros originales.
"""
import argparse
import csv
import getpass
import os
import sys
from collections import Counter
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / 'datos' / 'aprobacion_campus_explicitos_cdmx.csv'
CDMX = 'CIUDAD DE MÉXICO'
NIVEL = 'LICENCIATURA'
ESPERADO = 2810


def limpiar(valor):
    return ' '.join((valor or '').split()).strip()


def correspondencias():
    if not CSV_PATH.exists():
        raise RuntimeError(f'No existe el CSV: {CSV_PATH}')
    resultado = {}
    with CSV_PATH.open(encoding='utf-8-sig', newline='') as archivo:
        for fila in csv.DictReader(archivo):
            if limpiar(fila['decision_manual']).upper() != 'APROBAR':
                continue
            nombre = limpiar(fila['nombre_en_pdf'])
            institucion = limpiar(fila['institucion_aprobada'])
            plantel = limpiar(fila['plantel_aprobado'])
            if not nombre or not institucion or not plantel:
                raise RuntimeError(f'Correspondencia aprobada incompleta: {nombre}')
            if (institucion != limpiar(fila['institucion_propuesta'])
                    or plantel != limpiar(fila['plantel_propuesto'])):
                raise RuntimeError(f'La correspondencia fue modificada: {nombre}')
            if nombre in resultado and resultado[nombre] != (institucion, plantel):
                raise RuntimeError(f'Correspondencia contradictoria: {nombre}')
            resultado[nombre] = (institucion, plantel)
    return resultado


def consulta_origen(cur):
    cur.execute('''
        SELECT id_registro,
               btrim(datos_json->>'institucion'),
               btrim(datos_json->>'programa'),
               btrim(datos_json->>'modalidad'),
               COALESCE(datos_json->>'acuerdo_rvoe_fecha','')
        FROM origen.registro_origen
        WHERE btrim(datos_json->>'estado') = %s
          AND btrim(datos_json->>'nivel_estudios') = %s
        ORDER BY id_registro
    ''', (CDMX, NIVEL))
    return cur.fetchall()


def obtener_catalogo(cur, tabla, clave, valor):
    cur.execute(f'SELECT {clave} FROM catalogo.{tabla} WHERE nombre = %s', (valor,))
    coincidencias = cur.fetchall()
    if len(coincidencias) != 1:
        raise RuntimeError(f'Catálogo {tabla}: se esperaba una fila para {valor!r}; hay {len(coincidencias)}')
    return coincidencias[0][0]


def ejecutar(aplicar):
    aprobadas = correspondencias()
    usuario = os.getenv('PGUSER', 'postgres')
    password = os.getenv('PGPASSWORD') or getpass.getpass(f'Contraseña PostgreSQL ({usuario}): ')
    conexion = psycopg2.connect(host=os.getenv('PGHOST', 'localhost'),
                                port=os.getenv('PGPORT', '5432'),
                                dbname='oferta_educativa', user=usuario, password=password)
    try:
        with conexion:
            with conexion.cursor() as cur:
                filas = consulta_origen(cur)
                if len(filas) != ESPERADO:
                    raise RuntimeError(f'Esperábamos {ESPERADO} registros CDMX; hay {len(filas)}')
                # Si hay registros sin identificadores esenciales, no crear entidades ficticias.
                invalidas = [r[0] for r in filas if any(not limpiar(x) for x in r[1:4])]
                if invalidas:
                    raise RuntimeError(f'{len(invalidas)} filas sin institución/programa/modalidad; ejemplos de ID: {invalidas[:10]}')
                cur.execute('''SELECT COUNT(*) FROM origen.vinculo_registro v
                    JOIN origen.registro_origen r ON r.id_registro=v.id_registro
                    WHERE btrim(r.datos_json->>'estado')=%s
                    AND btrim(r.datos_json->>'nivel_estudios')=%s''', (CDMX, NIVEL))
                vinculados = cur.fetchone()[0]
                if vinculados:
                    raise RuntimeError(f'Ya existen {vinculados} vínculos de licenciaturas CDMX. No se duplica una carga previa.')

                tipos = Counter('plantel explícito' if limpiar(r[1]) in aprobadas
                                else 'denominación original provisional' for r in filas)
                nombres = set(limpiar(r[1]) for r in filas)
                print(f'Registros de licenciaturas CDMX: {len(filas)}')
                print(f'Denominaciones originales distintas: {len(nombres)}')
                print(f'Correspondencias aprobadas presentes: {len(nombres & aprobadas.keys())}')
                for k, v in tipos.items():
                    print(f'{k}: {v}')
                print('Las otras denominaciones se conservan completas; el plantel queda sin identificar (NULL).')
                if not aplicar:
                    print('SIMULACIÓN: no se ha insertado ningún registro.')
                    return

                id_estado = obtener_catalogo(cur, 'estado', 'id_estado', CDMX)
                id_nivel = obtener_catalogo(cur, 'nivel_academico', 'id_nivel', NIVEL)
                cur.execute('SELECT nombre, id_modalidad FROM catalogo.modalidad')
                modos = dict(cur.fetchall())
                cur.execute('SELECT nombre, id_programa FROM catalogo.programa_academico WHERE id_nivel=%s', (id_nivel,))
                programas = dict(cur.fetchall())
                cur.execute('SELECT nombre, id_institucion FROM catalogo.institucion')
                instituciones = {}
                for nombre, ident in cur.fetchall():
                    if nombre in instituciones:
                        raise RuntimeError(f'Institución duplicada: {nombre}')
                    instituciones[nombre] = ident
                cur.execute('''SELECT p.id_institucion, p.nombre, p.id_plantel
                               FROM catalogo.plantel p WHERE p.id_estado=%s''', (id_estado,))
                planteles = {}
                for i, nombre, ident in cur.fetchall():
                    key = (i, nombre)
                    if key in planteles:
                        raise RuntimeError(f'Plantel duplicado: {key}')
                    planteles[key] = ident
                # Solo se reutilizan ofertas existentes con vínculo documentado; no
                # asumimos que otras ofertas sin procedencia sean equivalentes.
                oferta_por_tupla = {}
                autorizacion_por_tupla = {}
                nuevos = Counter()
                for id_reg, nombre_original, programa, modalidad, acuerdo in filas:
                    nombre_original = limpiar(nombre_original)
                    programa, modalidad = limpiar(programa), limpiar(modalidad)
                    if programa not in programas or modalidad not in modos:
                        raise RuntimeError(f'Falta un programa o modalidad en catálogo: registro {id_reg}')
                    institucion, plantel = aprobadas.get(nombre_original, (nombre_original, None))
                    if institucion not in instituciones:
                        cur.execute('INSERT INTO catalogo.institucion(nombre) VALUES(%s) RETURNING id_institucion', (institucion,))
                        instituciones[institucion] = cur.fetchone()[0]
                        nuevos['instituciones'] += 1
                    id_inst = instituciones[institucion]
                    llave_plantel = (id_inst, plantel)
                    if llave_plantel not in planteles:
                        cur.execute('''INSERT INTO catalogo.plantel(id_institucion,id_estado,nombre)
                                       VALUES(%s,%s,%s) RETURNING id_plantel''', (id_inst,id_estado,plantel))
                        planteles[llave_plantel] = cur.fetchone()[0]
                        nuevos['planteles'] += 1
                    id_plantel = planteles[llave_plantel]
                    llave_oferta = (id_plantel, programas[programa], modos[modalidad])
                    if llave_oferta not in oferta_por_tupla:
                        cur.execute('''INSERT INTO catalogo.oferta_educativa(id_plantel,id_programa,id_modalidad)
                                       VALUES (%s,%s,%s) RETURNING id_oferta''', llave_oferta)
                        oferta_por_tupla[llave_oferta] = cur.fetchone()[0]
                        nuevos['ofertas'] += 1
                    id_oferta = oferta_por_tupla[llave_oferta]
                    id_autorizacion = None
                    # Preservar el texto completo sin deducir fechas a partir de valores dudosos.
                    if acuerdo and acuerdo.strip():
                        llave_auto = (id_oferta, acuerdo)
                        if llave_auto not in autorizacion_por_tupla:
                            cur.execute('''INSERT INTO catalogo.autorizacion(id_oferta,texto_original)
                                           VALUES(%s,%s) RETURNING id_autorizacion''', (id_oferta, acuerdo))
                            autorizacion_por_tupla[llave_auto] = cur.fetchone()[0]
                            nuevos['autorizaciones'] += 1
                        id_autorizacion = autorizacion_por_tupla[llave_auto]
                    cur.execute('''INSERT INTO origen.vinculo_registro
                                   (id_registro,id_oferta,id_autorizacion,estado_revision)
                                   VALUES (%s,%s,%s,'REVISAR')''', (id_reg,id_oferta,id_autorizacion))
                    nuevos['vinculos'] += 1
                if nuevos['vinculos'] != ESPERADO:
                    raise RuntimeError('Carga incompleta: se revierte toda la transacción')
                print('Insertados en esta transacción:', dict(nuevos))
                print('Los 2810 vínculos quedan como REVISAR hasta validar las identidades y autorizaciones.')
        print('TRANSACCIÓN CONFIRMADA.')
    finally:
        conexion.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Aplicar la carga luego de simular')
    args = parser.parse_args()
    try:
        ejecutar(args.apply)
    except Exception as exc:
        sys.exit(f'ERROR: {exc}')
