"""Regresión para interacciones compuestas y consultas académicas."""

import pytest

from motor_ia import interaccion_general as mod

@pytest.mark.parametrize('pregunta', [
    'Buenas noches, ¿en qué me puede ayudar este asistente?',
    'Hola, ¿qué puedes hacer?',
    '¿En qué me puedes ayudar?',
    'Buenas tardes, ¿qué consultas puedo hacer?',
])
def test_consultas_de_capacidades(pregunta):
    respuesta = mod.detectar_interaccion_general(pregunta)
    assert respuesta is not None
    assert respuesta['cerrar'] is False
    assert 'Puedo buscar carreras' in respuesta['mensaje']

@pytest.mark.parametrize('pregunta', [
    'Muchas gracias por la información. Hasta pronto.',
    'Gracias por la orientación; nos vemos pronto.',
    'Muchas gracias, hasta luego.',
    'Gracias por tu ayuda, adiós.',
])
def test_despedidas_compuestas(pregunta):
    respuesta = mod.detectar_interaccion_general(pregunta)
    assert respuesta is not None
    assert respuesta['cerrar'] is True

@pytest.mark.parametrize('pregunta', [
    'Hola, ¿qué carreras ofrece la Universidad La Salle?',
    'Buenas noches, ¿qué universidades ofrecen Psicología?',
    'Gracias, ¿cuáles de esas carreras son mixtas?',
    'Muchas gracias por la información, ¿cuáles son escolarizadas?',
    '¿Cómo funcionan las antenas?',
])
def test_consultas_academicas_no_interceptadas(pregunta):
    assert mod.detectar_interaccion_general(pregunta) is None


def test_becas_siguen_con_prioridad():
    r = mod.detectar_interaccion_general('Buenas tardes, ¿qué becas ofrecen?')
    assert 'becas' in r['mensaje']
    assert r['cerrar'] is False
