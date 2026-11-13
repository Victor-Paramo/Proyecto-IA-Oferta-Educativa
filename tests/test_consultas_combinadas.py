"""Regresión de filtros combinados sobre ofertas previamente recuperadas.

No requiere datos privados, PostgreSQL ni descarga de MiniLM.
"""
import ast
from pathlib import Path

import pytest


APP = Path(__file__).resolve().parents[1] / 'app.py'
ARBOL = ast.parse(APP.read_text(encoding='utf-8'))
NOMBRES = {'filtrar_ofertas_combinadas', 'seleccionar_programas_de_institucion'}
FUNCIONES = [n for n in ARBOL.body if isinstance(n, ast.FunctionDef) and n.name in NOMBRES]
AMBIENTE = {}
exec(compile(ast.Module(body=FUNCIONES, type_ignores=[]), str(APP), 'exec'), AMBIENTE)
filtrar = AMBIENTE['filtrar_ofertas_combinadas']
seleccionar = AMBIENTE['seleccionar_programas_de_institucion']

OFERTAS = [
    {'institucion': 'UNIVERSIDAD ICEL', 'modalidad': 'ESCOLARIZADA'},
    {'institucion': 'UNIVERSIDAD ICEL', 'modalidad': 'MIXTA'},
    {'institucion': 'INSTITUTO SAE', 'modalidad': 'MIXTA'},
]
ICEL = {'nombre': 'UNIVERSIDAD ICEL'}
SAE = {'nombre': 'INSTITUTO SAE'}


@pytest.mark.parametrize('institucion,modalidad,esperados', [
    (None, None, 3), (ICEL, None, 2), (SAE, None, 1),
    (ICEL, 'MIXTA', 1), (ICEL, 'ESCOLARIZADA', 1),
    (SAE, 'ESCOLARIZADA', 0), (None, 'MIXTA', 2),
])
def test_filtros_combinados(institucion, modalidad, esperados):
    assert len(filtrar(OFERTAS, institucion, modalidad)) == esperados


def test_seleccion_de_programas_antes_de_ordenar():
    def simular_busqueda(_conexion, id_programa):
        return {
            1: [OFERTAS[2]],
            2: [OFERTAS[0]],
            3: [OFERTAS[1]],
        }[id_programa]
    AMBIENTE['buscar_programa'] = simular_busqueda
    assert seleccionar(None, [(1, 'ARTES'), (2, 'BIOMEDICA'), (3, 'TECNOLOGIA')], ICEL) == [
        (2, 'BIOMEDICA'), (3, 'TECNOLOGIA')
    ]
    assert seleccionar(None, [(1, 'ARTES'), (2, 'BIOMEDICA'), (3, 'TECNOLOGIA')], ICEL, 'MIXTA') == [
        (3, 'TECNOLOGIA')
    ]


def evaluar_enrutamiento(pregunta, interpretacion, temas, seguimiento=False,
                         exploracion_por_clasificador=False):
    """Ejecuta las decisiones reales de enrutamiento sin importar app.py.

    Solo se evalúan las asignaciones pertinentes del AST, usando funciones
    simuladas; no depende del formato textual ni inicia PostgreSQL/MiniLM.
    """
    asignaciones = {}
    for nodo in ast.walk(ARBOL):
        if isinstance(nodo, ast.Assign) and len(nodo.targets) == 1:
            objetivo = nodo.targets[0]
            if isinstance(objetivo, ast.Name) and objetivo.id in {
                'exploracion_explicita', 'consulta_combinada', 'explorar_tema'
            }:
                asignaciones[objetivo.id] = nodo.value

    assert set(asignaciones) == {
        'exploracion_explicita', 'consulta_combinada', 'explorar_tema'
    }

    ambiente = {
        'hay_tema': bool(temas),
        'pregunta': pregunta,
        'interpretacion': interpretacion,
        'seguimiento_estructurado': seguimiento,
        'es_peticion_exploratoria_explicita': lambda texto: 'algo relacionado con' in texto.lower(),
        'es_exploracion_tematica': lambda _inter: exploracion_por_clasificador,
    }
    for nombre in ('exploracion_explicita', 'consulta_combinada', 'explorar_tema'):
        expresion = ast.Expression(body=asignaciones[nombre])
        ast.fix_missing_locations(expresion)
        ambiente[nombre] = eval(compile(expresion, str(APP), 'eval'), ambiente)
    return ambiente['explorar_tema']


@pytest.mark.parametrize('pregunta,programa,institucion,hay_tema,seguimiento,esperado', [
    ('Quiero estudiar algo relacionado con ciencia de datos en UVM',
     {'id_programa': 1}, ICEL, True, False, True),
    ('Quiero estudiar algo relacionado con animacion digital en ICEL',
     None, ICEL, True, False, True),
    ('Quiero estudiar algo relacionado con ciencia de datos',
     {'id_programa': 1}, None, True, False, True),
    ('La universidad ICEL ofrece Ingenieria en Ciencia de Datos',
     {'id_programa': 2}, ICEL, True, False, False),
    ('Que programas ofrece ICEL', None, ICEL, False, False, False),
    ('Y cuales de esas opciones son mixtas', None, ICEL, True, True, False),
])
def test_enrutamiento_tematica_frente_a_busqueda_exacta(
        pregunta, programa, institucion, hay_tema, seguimiento, esperado):
    interpretacion = {'programa': programa, 'institucion': institucion}
    assert evaluar_enrutamiento(
        pregunta, interpretacion, hay_tema, seguimiento
    ) is esperado


def test_clasificador_tambien_puede_activar_exploracion():
    assert evaluar_enrutamiento(
        'Me interesan los planetas',
        {'programa': None, 'institucion': None},
        temas=True, exploracion_por_clasificador=True
    ) is True
