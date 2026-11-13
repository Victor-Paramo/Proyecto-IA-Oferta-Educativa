"""Regresiones de cobertura temática (sin PostgreSQL ni descargar MiniLM)."""
import pytest

from motor_ia.validacion_cobertura_tematica import (
    detectar_temas,
    priorizar_temas,
    construir_indice,
    comprobar_cobertura,
    es_exploracion_tematica,
)
from motor_ia.descripciones_tematicas import describir_por_nombre


CATALOGO_EJEMPLO = [
    (1, "EN MATEMÁTICAS APLICADAS"),
    (2, "EN INGENIERÍA AERONÁUTICA"),
    (3, "EN ASTRONOMÍA"),
    (4, "EN INGENIERÍA AEROESPACIAL"),
    (5, "EN ARQUEOLOGÍA"),
    (6, "EN PALEONTOLOGÍA"),
    (7, "EN METEOROLOGÍA"),
    (8, "EN DISEÑO DE VIDEOJUEGOS"),
    (9, "EN INGENIERÍA EN SOFTWARE"),
    (10, "EN PSICOLOGÍA"),
    (11, "EN INGENIERÍA ELECTRÓNICA"),
    (12, "EN TURISMO INTERNACIONAL"),
]


@pytest.mark.parametrize("pregunta,area", [
    ("Me gustan las matemáticas y resolver problemas de lógica.", "matematicas"),
    ("Quiero aprender razonamiento lógico.", "matematicas"),
    ("Me gustaría investigar la formación de nubes de tormenta.", "meteorologia"),
    ("Quiero pronosticar huracanes.", "meteorologia"),
    ("Me interesa estudiar satélites y sondas espaciales.", "aeroespacial"),
    ("Quiero dedicarme al estudio de satélites y sondas espaciales.", "aeroespacial"),
    ("Me interesa el diseño de aviones comerciales.", "aeronautica"),
    ("Me gustaría investigar planetas y estrellas lejanas.", "astronomia"),
    ("Quiero estudiar dinosaurios y fósiles.", "paleontologia"),
    ("Me gustaría desarrollar videojuegos y programar mundos virtuales.", "videojuegos"),
    ("Quiero construir robots industriales.", "robotica"),
    ("Quiero estudiar el comportamiento humano.", "psicologia"),
])
def test_reconoce_interes(pregunta, area):
    assert area in detectar_temas(pregunta)


def test_etiquetas_inferidas_por_titulo_no_confunden_especialidades():
    assert describir_por_nombre("EN MATEMÁTICAS APLICADAS")[1] == ["matematicas"]
    assert describir_por_nombre("EN INGENIERÍA AERONÁUTICA")[1] == ["aeronautica"]
    assert describir_por_nombre("EN INGENIERÍA AEROESPACIAL")[1] == ["aeroespacial"]
    assert describir_por_nombre("EN PALEONTOLOGÍA")[1] == ["paleontologia"]


def test_indice_no_confunde_areas():
    indice = construir_indice(CATALOGO_EJEMPLO)
    assert {id for id, _ in indice["astronomia"]} == {3}
    assert {id for id, _ in indice["aeroespacial"]} == {4}
    assert {id for id, _ in indice["aeronautica"]} == {2}
    assert {id for id, _ in indice["arqueologia"]} == {5}
    assert {id for id, _ in indice["paleontologia"]} == {6}
    assert {id for id, _ in indice["matematicas"]} == {1}


@pytest.mark.parametrize("pregunta,programa", [
    ("Me gustan las matemáticas y resolver problemas de lógica.", 1),
    ("Me gustaría investigar la formación de nubes de tormenta.", 7),
    ("Quiero estudiar satélites y sondas espaciales.", 4),
    ("Me interesa el diseño de aviones comerciales.", 2),
])
def test_cobertura_directa_con_titulo_explicito(pregunta, programa):
    r = comprobar_cobertura(pregunta, construir_indice(CATALOGO_EJEMPLO))
    assert r["estado"] == "cobertura_directa"
    assert r["ids_validos"] == {programa}


def test_sin_cobertura_no_recomienda_otras_carreras():
    indice = construir_indice([(1, "EN GASTRONOMÍA"), (2, "EN PSICOLOGÍA")])
    r = comprobar_cobertura("Me gustaría investigar la formación de nubes de tormenta", indice)
    assert r["estado"] == "sin_cobertura_directa"
    assert r["ids_validos"] == set()


def test_no_confunde_videojuegos_y_software_generico():
    temas = detectar_temas("Me gustaría programar videojuegos")
    assert {"software", "videojuegos"}.issubset(set(temas))
    assert priorizar_temas(temas) == ["videojuegos"]


def test_interes_rescatado_sin_filtros():
    i = {"intencion": "buscar_institucion", "pregunta": "Me gustan las matemáticas y la lógica",
         "institucion": None, "programa": None, "modalidad": None}
    assert es_exploracion_tematica(i)


def test_no_sobrescribe_consulta_de_carrera_especifica():
    i = {"intencion": "buscar_programa", "pregunta": "Quiero estudiar Matemáticas Aplicadas",
         "institucion": None, "programa": {"id_programa": 1, "nombre": "EN MATEMÁTICAS APLICADAS"}, "modalidad": None}
    assert not es_exploracion_tematica(i)


def test_no_sobrescribe_modalidad():
    i = {"intencion": "filtrar_modalidad", "pregunta": "No quiero modalidad mixta",
         "institucion": None, "programa": None, "modalidad": "MIXTA"}
    assert not es_exploracion_tematica(i)


def test_no_inventa_area_para_pregunta_vaga():
    assert detectar_temas("No sé qué estudiar") == []
    assert comprobar_cobertura("No sé qué estudiar", construir_indice(CATALOGO_EJEMPLO))["estado"] == "aclaracion"
