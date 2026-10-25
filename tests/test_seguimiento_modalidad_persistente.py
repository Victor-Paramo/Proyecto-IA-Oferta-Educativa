"""Regresiones: conservación explícita de filtros en preguntas de seguimiento."""

import pytest

from motor_ia.contexto import actualizar_contexto, crear_contexto


@pytest.fixture
def contexto_derecho():
    contexto = crear_contexto()
    contexto["institucion"] = {"id_institucion": 10, "nombre": "UNIVERSIDAD ICEL"}
    contexto["programa"] = {"id_programa": 30, "nombre": "DERECHO"}
    return contexto


@pytest.mark.parametrize("pregunta, modalidad", [
    ("No quiero modalidad mixta; muéstrame solamente las escolarizadas.", "ESCOLARIZADA"),
    ("¿Y si cambio a una modalidad completamente a distancia?", "NO ESCOLARIZADA"),
    ("¿Y si después prefiero una modalidad mixta?", "MIXTA"),
])
def test_cambio_de_modalidad_conserva_carrera_e_institucion(contexto_derecho, pregunta, modalidad):
    interpretacion = {"pregunta": pregunta, "institucion": None,
                      "programa": None, "modalidad": modalidad}
    nuevo = actualizar_contexto(contexto_derecho, interpretacion, conservar=True)
    assert nuevo["programa"] == contexto_derecho["programa"]
    assert nuevo["institucion"] == contexto_derecho["institucion"]
    assert nuevo["modalidad"] == modalidad


def test_consulta_nueva_no_hereda_carrera_anterior(contexto_derecho):
    interpretacion = {"pregunta": "Quiero estudiar Psicología.",
                      "institucion": None,
                      "programa": {"id_programa": 70, "nombre": "PSICOLOGÍA"},
                      "modalidad": None}
    nuevo = actualizar_contexto(contexto_derecho, interpretacion, conservar=False)
    assert nuevo["institucion"] is None
    assert nuevo["programa"]["nombre"] == "PSICOLOGÍA"
    assert nuevo["modalidad"] is None


def test_seguimiento_de_programas_semanticos_no_pierde_ids():
    contexto = crear_contexto()
    contexto["programas_semanticos"] = [12, 15]
    contexto["institucion"] = {"id_institucion": 4, "nombre": "UNIVERSIDAD LA SALLE"}
    interpretacion = {"pregunta": "¿Y si después prefiero una modalidad mixta?",
                      "institucion": None, "programa": None, "modalidad": "MIXTA"}
    nuevo = actualizar_contexto(contexto, interpretacion, conservar=True)
    assert nuevo["programas_semanticos"] == [12, 15]
    assert nuevo["institucion"] == contexto["institucion"]
    assert nuevo["modalidad"] == "MIXTA"


def test_comportamiento_previo_sin_argumento_conservar(contexto_derecho):
    interpretacion = {"pregunta": "¿Cuáles de esas opciones son mixtas?",
                      "institucion": None, "programa": None, "modalidad": "MIXTA"}
    nuevo = actualizar_contexto(contexto_derecho, interpretacion)
    assert nuevo["programa"] == contexto_derecho["programa"]
