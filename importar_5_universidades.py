"""Carga unica de catalogos de 5 universidades, con trazabilidad y datos provisionales.
Requiere psycopg2, PostgreSQL y catalogo_5_universidades_revision.csv.
"""
import csv
import getpass
import os
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
import psycopg2

SOURCE = Path(__file__).with_name('catalogo_5_universidades_revision.csv')
PLACEHOLDER = 'SEDE CDMX POR CONFIRMAR (CATÁLOGO NACIONAL)'
UNKNOWN_MODE = 'NO ESPECIFICADA'

def norm(s):
    s = ''.join(ch for ch in unicodedata.normalize('NFD', str(s or '').upper()) if unicodedata.category(ch) != 'Mn')
    return ' '.join(re.sub(r'[^A-Z0-9]+', ' ', s).split())

def prog(s):
    s=norm(s)
    for prefix in ('LICENCIATURA EN ', 'LICENCIATURA ', 'EN '):
        if s.startswith(prefix): return s[len(prefix):]
    return s

def main():
    with SOURCE.open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    if not rows: raise RuntimeError('No se encontraron filas en el CSV')
    passwd=os.environ.get('PGPASSWORD') or getpass.getpass('Contraseña PostgreSQL: ')
    conn=psycopg2.connect(host=os.getenv('PGHOST','localhost'),port=os.getenv('PGPORT','5432'),dbname=os.getenv('PGDATABASE','oferta_educativa'),user=os.getenv('PGUSER','postgres'),password=passwd)
    counts=Counter()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id_estado FROM catalogo.estado WHERE nombre=%s",('CIUDAD DE MÉXICO',))
                a=cur.fetchall()
                if len(a)!=1: raise RuntimeError('Estado CDMX no encontrado o duplicado')
                eid=a[0][0]
                cur.execute("SELECT id_nivel FROM catalogo.nivel_academico WHERE nombre=%s",('LICENCIATURA',))
                a=cur.fetchall()
                if len(a)!=1: raise RuntimeError('Nivel LICENCIATURA no encontrado o duplicado')
                nid=a[0][0]
                cur.execute('SELECT id_institucion,nombre FROM catalogo.institucion')
                inst={}
                for id_,name in cur.fetchall():inst.setdefault(norm(name),[]).append(id_)
                cur.execute('SELECT id_modalidad,nombre FROM catalogo.modalidad')
                modes={}
                for id_,name in cur.fetchall():modes.setdefault(norm(name),[]).append(id_)
                cur.execute('SELECT id_programa,nombre FROM catalogo.programa_academico WHERE id_nivel=%s',(nid,))
                programs={}
                for id_,name in cur.fetchall():programs.setdefault(prog(name),[]).append(id_)
                cur.execute('SELECT id_plantel,id_institucion,nombre FROM catalogo.plantel WHERE id_estado=%s',(eid,))
                sites={}
                for id_,iid,name in cur.fetchall():sites.setdefault((iid,norm(name)),[]).append(id_)
                cur.execute('''SELECT o.id_oferta,p.id_institucion,o.id_plantel,o.id_programa,o.id_modalidad
                    FROM catalogo.oferta_educativa o JOIN catalogo.plantel p ON p.id_plantel=o.id_plantel
                    WHERE p.id_estado=%s''',(eid,))
                offers={}
                existing_by_inst_program=set()
                for oid,iid,sid,pid,mid in cur.fetchall():
                    offers.setdefault((sid,pid,mid),[]).append(oid)
                    existing_by_inst_program.add((iid,pid))
                cur.execute('''CREATE TABLE IF NOT EXISTS catalogo.fuente_externa_oferta (
                    id_oferta BIGINT NOT NULL REFERENCES catalogo.oferta_educativa(id_oferta),
                    fuente_url TEXT NOT NULL,
                    institucion_fuente TEXT NOT NULL,
                    programa_fuente TEXT NOT NULL,
                    plantel_fuente TEXT NOT NULL,
                    modalidad_fuente TEXT NOT NULL,
                    fecha_consulta DATE NOT NULL DEFAULT CURRENT_DATE,
                    PRIMARY KEY(id_oferta,fuente_url)
                )''')
                cur.execute('''CREATE TABLE IF NOT EXISTS catalogo.catalogo_externo_revision (
                    id_revision BIGSERIAL PRIMARY KEY,
                    institucion TEXT NOT NULL,
                    programa TEXT NOT NULL,
                    plantel_reportado TEXT,
                    modalidad_reportada TEXT,
                    estado_reportado TEXT,
                    fuente_url TEXT NOT NULL,
                    estado_validacion TEXT NOT NULL,
                    id_oferta BIGINT REFERENCES catalogo.oferta_educativa(id_oferta),
                    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(institucion,programa,plantel_reportado,modalidad_reportada,fuente_url)
                )''')
                def unique(items,what):
                    if len(items)>1:raise RuntimeError('Ambigüedad: '+what)
                    return items[0] if items else None
                def ensure(map_,key,sql,params,description):
                    found=unique(map_.get(key,[]),description)
                    if found is None:
                        cur.execute(sql,params)
                        found=cur.fetchone()[0]
                        map_[key]=[found]
                    return found
                # La modalidad no documentada se conserva como NO ESPECIFICADA; no se inventa escolarizada.
                if UNKNOWN_MODE not in modes:
                    cur.execute('INSERT INTO catalogo.modalidad(nombre) VALUES (%s) RETURNING id_modalidad',(UNKNOWN_MODE,))
                    modes[UNKNOWN_MODE]=[cur.fetchone()[0]]
                for r in rows:
                    institution=r['institucion'].strip()
                    program=r['programa'].strip()
                    if not institution or not program: raise RuntimeError('Fila sin institución o programa')
                    campus=(r['plantel'] or '').strip() or PLACEHOLDER
                    modality=(r['modalidad'] or '').strip() or UNKNOWN_MODE
                    verified=(r['estado']=='CIUDAD DE MÉXICO' and bool(r['plantel']) and bool(r['modalidad']))
                    review_status='OFERTA_CDMX_DOCUMENTADA' if verified else 'PROVISIONAL_SIN_ACREDITAR_SEDE_Y_O_MODALIDAD_CDMX'
                    iid=ensure(inst,norm(institution),'INSERT INTO catalogo.institucion(nombre) VALUES (%s) RETURNING id_institucion',(institution,),institution)
                    pid=ensure(programs,prog(program),'INSERT INTO catalogo.programa_academico(id_nivel,nombre) VALUES (%s,%s) RETURNING id_programa',(nid,program),program)
                    mid=ensure(modes,norm(modality),'INSERT INTO catalogo.modalidad(nombre) VALUES (%s) RETURNING id_modalidad',(modality,),modality)
                    # Si ya existe oferta de ese programa para la misma institución en CDMX,
                    # no agregamos una supuesta sede adicional cuando la sede fuente es desconocida.
                    if not r['plantel'] and (iid,pid) in existing_by_inst_program:
                        counts['omitidas_por_existencia']+=1
                        oid=None
                    else:
                        site_key=(iid,norm(campus))
                        sid=ensure(sites,site_key,'INSERT INTO catalogo.plantel(id_institucion,id_estado,nombre) VALUES (%s,%s,%s) RETURNING id_plantel',(iid,eid,campus),campus)
                        okey=(sid,pid,mid)
                        oid=unique(offers.get(okey,[]),f'oferta {institution} {program}')
                        if oid is None:
                            cur.execute('INSERT INTO catalogo.oferta_educativa(id_plantel,id_programa,id_modalidad) VALUES (%s,%s,%s) RETURNING id_oferta',(sid,pid,mid))
                            oid=cur.fetchone()[0]
                            offers[okey]=[oid]
                            existing_by_inst_program.add((iid,pid))
                            counts['ofertas_nuevas']+=1
                        else: counts['ofertas_ya_existentes']+=1
                        cur.execute('''INSERT INTO catalogo.fuente_externa_oferta
                            (id_oferta,fuente_url,institucion_fuente,programa_fuente,plantel_fuente,modalidad_fuente)
                            VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING''',
                            (oid,r['fuente_url'],institution,program,campus,modality))
                    cur.execute('''INSERT INTO catalogo.catalogo_externo_revision
                        (institucion,programa,plantel_reportado,modalidad_reportada,estado_reportado,fuente_url,estado_validacion,id_oferta)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT(institucion,programa,plantel_reportado,modalidad_reportada,fuente_url)
                        DO UPDATE SET estado_validacion=EXCLUDED.estado_validacion,
                          id_oferta=COALESCE(catalogo.catalogo_externo_revision.id_oferta,EXCLUDED.id_oferta)''',
                        (institution,program,r['plantel'],r['modalidad'],r['estado'],r['fuente_url'],review_status,oid))
                    counts['filas_fuente']+=1
                    if verified:counts['sede_y_modalidad_documentadas']+=1
                    else:counts['provisionales']+=1
                print('CARGA COMPLETA DE CINCO UNIVERSIDADES')
                for key,val in counts.items():print(f'{key}: {val}')
                print('IMPORTANTE: las ofertas provisionales NO acreditan que la carrera se imparta en CDMX.')
                print('La respuesta actual del asistente solo cita SEP 2021; debe actualizarse para mencionar estas fuentes.')
    finally:conn.close()

if __name__=='__main__':
    try:main()
    except Exception as exc:sys.exit(f'ERROR (sin confirmar cambios de la transacción): {exc}')
