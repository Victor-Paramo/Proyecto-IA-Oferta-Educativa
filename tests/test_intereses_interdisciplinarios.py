"""Regresión de intereses interdisciplinarios y límites de evidencia del catálogo."""

import pytest

from motor_ia.validacion_cobertura_tematica import (
    detectar_temas, priorizar_temas, construir_indice, comprobar_cobertura,
)
from motor_ia.afinidades_academicas import buscar_afinidades


@pytest.mark.parametrize('consulta,esperado', [
    ('Quiero aprender a diseñar prótesis robóticas que ayuden a las personas.', 'biomedica'),
    ('Me gustaría analizar información genética para estudiar enfermedades.', 'genetica'),
    ('Quiero crear experiencias interactivas utilizando realidad aumentada.', 'realidad_aumentada'),
    ('Me interesa comprender cómo se transmiten las señales entre antenas y satélites.', 'telecomunicaciones'),
    ('Quisiera estudiar cómo funcionan los sistemas de navegación de los aviones.', 'aeronautica'),
])
def test_reconoce_interes(consulta, esperado):
    assert esperado in detectar_temas(consulta)


def test_telecomunicaciones_prioridad_sobre_aeroespacial():
    temas = detectar_temas('Me interesa comprender cómo se transmiten las señales entre antenas y satélites.')
    assert 'telecomunicaciones' in priorizar_temas(temas)
    assert 'aeroespacial' not in priorizar_temas(temas)


def test_no_prometer_ingenieria_robotica_como_biomedica():
    indice = construir_indice([(1, 'INGENIERÍA MECATRÓNICA')])
    res = comprobar_cobertura('Quiero aprender a diseñar prótesis robóticas', indice)
    assert res['estado'] == 'sin_cobertura_directa'
    assert res['ids_validos'] == set()


def test_genetica_no_equivale_automaticamente_a_biotecnologia():
    indice = construir_indice([(2, 'BIOTECNOLOGÍA')])
    assert comprobar_cobertura('Analizar información genética', indice)['estado'] == 'sin_cobertura_directa'


def test_realidad_aumentada_no_equivale_a_videojuegos():
    indice = construir_indice([(3, 'DESARROLLO DE SOFTWARE INTERACTIVO Y VIDEOJUEGOS')])
    assert comprobar_cobertura('Crear realidad aumentada', indice)['estado'] == 'sin_cobertura_directa'


def test_titulo_biomedica_como_evidencia_directa():
    indice = construir_indice([(4, 'INGENIERÍA BIOMÉDICA')])
    assert comprobar_cobertura('Prótesis robóticas', indice)['ids_validos'] == {4}


def test_afinidades_solo_titulos_existentes():
    programas = [
        (1, 'INGENIERÍA MECATRÓNICA'),
        (2, 'INGENIERÍA EN BIOTECNOLOGÍA'),
        (3, 'DESARROLLO DE SOFTWARE INTERACTIVO Y VIDEOJUEGOS'),
        (4, 'LICENCIATURA EN GASTRONOMÍA'),
    ]
    for tema, esperado in [('biomedica', 1), ('genetica', 2), ('realidad_aumentada', 3)]:
        afines = buscar_afinidades([tema], programas)
        assert any(a['id_programa'] == esperado for a in afines)
        assert all(a['id_programa'] in {1, 2, 3} for a in afines)


def test_sin_afinidades_no_inventa_ofertas():
    assert buscar_afinidades(['genetica'], [(1, 'DERECHO')]) == []


def test_no_regresion_videojuegos_y_meteorologia():
    assert 'videojuegos' in detectar_temas('Quiero programar videojuegos y mundos virtuales')
    assert 'meteorologia' in detectar_temas('Quiero comprender por qué se forman los tornados')
