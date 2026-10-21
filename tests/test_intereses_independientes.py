"""Pruebas de reglas de temas y afinidades, sin base de datos ni MiniLM.

Las coincidencias de carreras se verifican con un catálogo pequeño simulado;
no son prueba de disponibilidad real de un programa.
"""
import pytest

from motor_ia.validacion_cobertura_tematica import (
    detectar_temas, priorizar_temas, construir_indice, comprobar_cobertura,
    es_exploracion_tematica,
)
from motor_ia.descripciones_tematicas import describir_por_nombre
from motor_ia.afinidades_academicas import buscar_afinidades


@pytest.mark.parametrize('pregunta,tema', [
    ('Me gustaría comprender por qué se forman los tornados.', 'meteorologia'),
    ('Quiero estudiar tornados y tormentas tropicales.', 'meteorologia'),
    ('Me interesa conocer los ciclones tropicales.', 'meteorologia'),
    ('Cambiando de tema, me gustaría estudiar terremotos y volcanes.', 'geologia'),
    ('Quiero analizar los sismos y las placas tectónicas.', 'geologia'),
    ('Me gustaría investigar las erupciones volcánicas.', 'geologia'),
    ('Quiero estudiar geociencias.', 'geologia'),
    ('Quiero usar datos para descubrir patrones y hacer predicciones.', 'ciencia_datos'),
    ('Me interesa el análisis de datos.', 'ciencia_datos'),
    ('Quiero trabajar con ciencia de datos.', 'ciencia_datos'),
    ('Me gustaría aprender minería de datos.', 'ciencia_datos'),
    ('Me interesa big data y modelos predictivos.', 'ciencia_datos'),
    ('Me gusta desarrollar videojuegos y programar mundos virtuales.', 'videojuegos'),
    ('Me gustan las matemáticas y resolver problemas de lógica.', 'matematicas'),
    ('Quiero conocer los satélites y sondas espaciales.', 'aeroespacial'),
])
def test_detectar_interes(pregunta, tema):
    assert tema in detectar_temas(pregunta)


@pytest.mark.parametrize('pregunta', [
    'Hola, ¿cómo estás?',
    '¿Cuánto cuesta la colegiatura?',
    '¿Qué universidad ofrece Derecho?',
    'Me gusta dibujar personajes de videojuegos.',
])
def test_no_inventa_tema_nuevo(pregunta):
    assert 'ciencia_datos' not in detectar_temas(pregunta)
    assert 'geologia' not in detectar_temas(pregunta)


def test_titulos_datos_se_basaran_en_nombre_explicito():
    enriquecido, temas = describir_por_nombre('EN INGENIERÍA EN CIENCIA DE DATOS')
    assert 'ciencia_datos' in temas
    assert 'Temas sugeridos' in enriquecido
    _, temas_genericos = describir_por_nombre('EN ADMINISTRACIÓN DE EMPRESAS')
    assert 'ciencia_datos' not in temas_genericos


def test_titulos_geologia_reconocidos():
    _, temas = describir_por_nombre('EN CIENCIAS DE LA TIERRA')
    assert 'geologia' in temas
    _, temas = describir_por_nombre('EN GEOLOGÍA')
    assert 'geologia' in temas


def test_no_confundir_fisica_escolar_con_ciencias_naturales():
    opciones = buscar_afinidades(['geologia'], [
        (101, 'EN EDUCACIÓN FÍSICA'),
        (102, 'EN FÍSICA'),
        (103, 'EN MATEMÁTICAS APLICADAS'),
    ])
    ids = [op['id_programa'] for op in opciones]
    assert 101 not in ids
    assert 102 in ids
    assert 103 in ids


def test_datos_directos_prioritarios_sobre_software_generico():
    assert priorizar_temas(['software', 'ciencia_datos']) == ['ciencia_datos']
    assert priorizar_temas(['software', 'videojuegos']) == ['videojuegos']


def test_cobertura_datos_solo_titulos_de_datos():
    indice = construir_indice([
        (7, 'EN INGENIERÍA EN CIENCIA DE DATOS'),
        (8, 'EN INGENIERÍA DE SOFTWARE'),
        (9, 'EN GASTRONOMÍA'),
    ])
    cobertura = comprobar_cobertura('Quiero usar datos para descubrir patrones y hacer predicciones.', indice)
    assert cobertura['estado'] == 'cobertura_directa'
    assert cobertura['ids_validos'] == {7}


def test_sin_cobertura_geologica_no_muestra_carreras_ajenas():
    indice = construir_indice([
        (31, 'EN GASTRONOMÍA'),
        (32, 'EN ADMINISTRACIÓN DE EMPRESAS'),
    ])
    cobertura = comprobar_cobertura('Cambiando de tema, me gustaría estudiar terremotos y volcanes.', indice)
    assert cobertura['estado'] == 'sin_cobertura_directa'
    assert not cobertura['ids_validos']
    assert cobertura['temas_prioritarios'] == ['geologia']


def test_afinidades_geologia_se_basaran_en_catalogo_no_fabricado():
    candidatos = buscar_afinidades(['geologia'], [
        (22, 'EN INGENIERÍA FÍSICA'),
        (23, 'EN MATEMÁTICAS APLICADAS'),
        (24, 'EN GASTRONOMÍA INTERNACIONAL'),
    ])
    assert {p['id_programa'] for p in candidatos} == {22, 23}
    assert all(p['area_afin'] in ('fisica', 'matematicas') for p in candidatos)


def test_datos_sin_titulo_directo_ofrece_solo_programas_reales():
    candidatos = buscar_afinidades(['ciencia_datos'], [
        (41, 'EN MATEMÁTICAS APLICADAS'),
        (42, 'EN INGENIERÍA DE SOFTWARE'),
        (43, 'EN DISEÑO DE VIDEOJUEGOS'),
    ])
    assert {p['id_programa'] for p in candidatos} == {41, 42}


def test_rescate_de_preguntas_de_interes_mal_clasificadas():
    interpretacion = {
        'pregunta': 'Cambiando de tema, me gustaría estudiar terremotos y volcanes.',
        'intencion': 'buscar_institucion',
        'institucion': None, 'programa': None, 'modalidad': None,
    }
    assert es_exploracion_tematica(interpretacion)


def test_consulta_especifica_no_se_desvia_a_exploracion():
    interpretacion = {
        'pregunta': 'Me gustaría cursar Ingeniería en Ciencia de Datos en Universidad X',
        'intencion': 'buscar_programa',
        'institucion': {'nombre': 'Universidad X'}, 'programa': None, 'modalidad': None,
    }
    assert not es_exploracion_tematica(interpretacion)


def test_modalidad_positiva_no_es_sustituida_por_tema():
    interpretacion = {
        'pregunta': 'Quiero estudiar ciencia de datos en modalidad mixta',
        'intencion': 'filtrar_modalidad',
        'institucion': None, 'programa': None, 'modalidad': 'MIXTA',
    }
    assert not es_exploracion_tematica(interpretacion)
