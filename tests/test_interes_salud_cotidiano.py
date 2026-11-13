"""Regresión para intereses médicos expresados en lenguaje cotidiano."""
import pytest
from motor_ia.validacion_cobertura_tematica import (
    detectar_temas, comprobar_cobertura, es_exploracion_tematica,
    construir_indice,
)

@pytest.mark.parametrize('pregunta', [
    'Quiero algo de curar gente',
    'quiero algo de curar con medicinas',
    'Me gustaría curar a las personas',
    'Quisiera curar con medicamentos',
    'Me interesa atender pacientes',
    'Quiero tratar a personas enfermas',
    'Quiero estudiar Medicina',
])
def test_interes_medico_explicito(pregunta):
    assert 'medicina' in detectar_temas(pregunta)

@pytest.mark.parametrize('pregunta', [
    'Quiero curar queso',
    'Quiero curar madera',
    'Quiero curar cemento',
    'Quiero desarrollar videojuegos',
])
def test_no_confundir_otros_usos_de_curar(pregunta):
    assert 'medicina' not in detectar_temas(pregunta)

@pytest.mark.parametrize('pregunta', [
    'Quiero algo de curar gente',
    'quiero algo de curar con medicinas',
])
def test_enrutamiento_exploratorio(pregunta):
    interpretacion = dict(pregunta=pregunta, intencion='buscar_programa',
                          institucion=None, programa=None, modalidad=None)
    assert es_exploracion_tematica(interpretacion)


def test_cobertura_directa_solo_con_catalogo():
    indice=construir_indice([(1,'MEDICINA'), (2,'ENFERMERÍA'), (3,'MERCADOTECNIA')])
    respuesta=comprobar_cobertura('Quiero algo de curar gente',indice)
    assert respuesta['estado']=='cobertura_directa'
    assert 1 in respuesta['ids_validos']
    assert 3 not in respuesta['ids_validos']
