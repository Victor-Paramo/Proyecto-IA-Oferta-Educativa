"""Regresión para distinguir solicitudes temáticas de títulos académicos exactos."""
import ast
import re
import unicodedata
from pathlib import Path


def normalizar_texto(mensaje):
    texto = unicodedata.normalize('NFD', mensaje.lower())
    return ''.join(c for c in texto if unicodedata.category(c) != 'Mn')


def _funcion():
    # Se obtiene solo la función de decisión: no requiere PostgreSQL ni MiniLM.
    ruta = Path(__file__).resolve().parents[1] / 'app.py'
    arbol = ast.parse(ruta.read_text(encoding='utf-8'))
    nodo = next(n for n in arbol.body if isinstance(n, ast.FunctionDef)
                and n.name == 'es_peticion_exploratoria_explicita')
    modulo = ast.Module(body=[nodo], type_ignores=[])
    espacio = {'re': re, 'normalizar_texto': normalizar_texto}
    exec(compile(modulo, str(ruta), 'exec'), espacio)
    return espacio[nodo.name]


def test_interes_explicito_ciencia_de_datos():
    assert _funcion()('Ahora quiero estudiar algo relacionado con ciencia de datos en la Universidad del Valle de México.')


def test_interes_explicito_animacion():
    assert _funcion()('Quiero explorar carreras relacionadas con animación digital en la Universidad Panamericana.')


def test_programa_exacto_no_es_exploracion():
    assert not _funcion()('¿La UVM ofrece Ingeniería en Ciencia de Datos?')


def test_programa_exacto_sin_ingenieria():
    assert not _funcion()('¿Dónde se ofrece Ciencia de Datos?')


def test_otra_carrera_exacta():
    assert not _funcion()('¿Dónde estudiar Psicología en modalidad mixta?')


def test_solicitud_institucion_sin_tema():
    assert not _funcion()('¿Qué carreras ofrece la Universidad ICEL?')
