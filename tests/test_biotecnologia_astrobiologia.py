"""Pruebas de reconocimiento y cobertura de especialidades de títulos SEP.

Los catálogos de prueba son sintéticos y no representan registros oficiales.
"""
from motor_ia.afinidades_academicas import buscar_afinidades
from motor_ia.descripciones_tematicas import describir_por_nombre
from motor_ia.validacion_cobertura_tematica import (
    comprobar_cobertura,
    construir_indice,
    detectar_temas,
    priorizar_temas,
)


def test_reconoce_interes_biotecnologia():
    assert 'biotecnologia' in detectar_temas(
        'Me interesa investigar cómo se desarrollan nuevos medicamentos utilizando biotecnología.'
    )


def test_reconoce_astrobiologia_como_especialidad():
    assert 'astrobiologia' in detectar_temas(
        '¿Existe una licenciatura en Astrobiología registrada en la Universidad ICEL?'
    )


def test_astrobiologia_no_se_confunde_con_astronomia():
    temas = detectar_temas('Quiero estudiar Astrobiología')
    assert 'astronomia' not in temas
    assert priorizar_temas(temas) == ['astrobiologia']


def test_cobertura_biotecnologia_solo_titulos_evidentes():
    indice = construir_indice([(1, 'BIOTECNOLOGÍA'), (2, 'DERECHO')])
    cobertura = comprobar_cobertura('Deseo estudiar biotecnología', indice)
    assert cobertura['estado'] == 'cobertura_directa'
    assert cobertura['ids_validos'] == {1}


def test_astrobiologia_no_acepta_biologia_como_programa_directo():
    indice = construir_indice([(1, 'BIOLOGÍA'), (2, 'ASTRONOMÍA'), (3, 'DERECHO')])
    cobertura = comprobar_cobertura('¿Puedo estudiar Astrobiología?', indice)
    assert cobertura['estado'] == 'sin_cobertura_directa'
    assert cobertura['ids_validos'] == set()


def test_astrobiologia_si_existe_titulo_explicito():
    indice = construir_indice([(1, 'ASTROBIOLOGÍA'), (2, 'BIOLOGÍA')])
    cobertura = comprobar_cobertura('Quiero Astrobiología', indice)
    assert cobertura['ids_validos'] == {1}


def test_afinidades_solo_de_titulos_reales_suministrados():
    catalogo = [(1, 'BIOLOGÍA'), (2, 'DERECHO'), (3, 'FÍSICA')]
    resultados = buscar_afinidades(['astrobiologia'], catalogo)
    assert resultados
    assert {r['nombre'] for r in resultados}.issubset({'BIOLOGÍA', 'FÍSICA'})
    assert all(r['id_programa'] != 2 for r in resultados)


def test_anotaciones_distinguen_especialidades():
    assert 'biotecnologia' in describir_por_nombre('INGENIERÍA EN BIOTECNOLOGÍA')[1]
    assert 'astrobiologia' in describir_por_nombre('ASTROBIOLOGÍA')[1]
    assert 'astrobiologia' not in describir_por_nombre('BIOLOGÍA')[1]
