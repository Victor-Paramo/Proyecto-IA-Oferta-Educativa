"""Verifica la agrupación por institución de resultados semánticos."""

from motor_ia.generador_respuestas import respuesta_programas


def _oferta(institucion, modalidad, plantel=None):
    return {'institucion': institucion, 'modalidad': modalidad, 'plantel': plantel}


def test_resumen_incluye_todas_las_modalidades_por_institucion():
    resultados = [{
        'programa': 'ENFERMERÍA',
        'ofertas': [
            _oferta('UNIVERSIDAD DEL VALLE DE MÉXICO', 'ESCOLARIZADA', 'SAN RAFAEL'),
            _oferta('UNIVERSIDAD DEL VALLE DE MÉXICO', 'ESCOLARIZADA', 'TLALPAN'),
            _oferta('UNIVERSIDAD TEC MILENIO FERRERÍA', 'MIXTA'),
        ],
    }]
    respuesta = respuesta_programas(resultados, ['medicina'])
    assert 'UNIVERSIDAD DEL VALLE DE MÉXICO | ENFERMERÍA' in respuesta
    assert 'UNIVERSIDAD TEC MILENIO FERRERÍA | ENFERMERÍA' in respuesta
    assert 'Modalidades: ESCOLARIZADA (2 ofertas registradas)' in respuesta
    assert 'Modalidades: MIXTA' in respuesta
    assert 'Planteles: SAN RAFAEL, TLALPAN' in respuesta


def test_no_atribuye_modalidad_a_institucion_incorrecta():
    resultados = [{'programa': 'ENFERMERÍA', 'ofertas': [
        _oferta('UNIVERSIDAD A', 'ESCOLARIZADA'),
        _oferta('UNIVERSIDAD B', 'MIXTA'),
    ]}]
    respuesta = respuesta_programas(resultados, ['medicina'])
    lineas = [l for l in respuesta.splitlines() if l.startswith('- ')]
    assert len(lineas) == 2
    assert any('UNIVERSIDAD A' in l and 'MIXTA' not in l for l in lineas)
    assert any('UNIVERSIDAD B' in l and 'ESCOLARIZADA' not in l for l in lineas)


def test_fichas_mantienen_cuatro_campos_para_interfaz():
    resultados = [{'programa': 'MEDICINA', 'ofertas': [_oferta('UNIVERSIDAD A', 'ESCOLARIZADA')]}]
    respuesta = respuesta_programas(resultados, ['medicina'])
    tarjeta = next(l for l in respuesta.splitlines() if l.startswith('- '))
    assert len(tarjeta[2:].split(' | ')) == 4


def test_sin_resultados_conserva_aviso():
    assert 'No encontré ofertas verificables' in respuesta_programas([], ['medicina'])

