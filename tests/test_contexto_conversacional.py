"""Pruebas de la correccion 2 de la etapa 4 (sin acceso a PostgreSQL).

Desde la raiz del proyecto:
    .\\.venv\\Scripts\\python.exe -m pytest tests/test_contexto_conversacional.py -v
"""

import pytest

from motor_ia.contexto import (
    crear_contexto,
    actualizar_contexto,
    es_seguimiento,
    es_seguimiento_estructurado,
)


@pytest.mark.parametrize("pregunta", [
    "¿Y cuáles de esas opciones son escolarizadas?",
    "Ahora muéstrame las opciones mixtas.",
    "¿Esa licenciatura se puede cursar en modalidad mixta?",
    "¿Se puede cursar esa carrera a distancia?",
    "¿Y cuáles son mixtas?",
    "Ahora solo las presenciales.",
    "¿Y las opciones no escolarizadas?",
])
def test_detecta_seguimientos(pregunta):
    assert es_seguimiento(pregunta)


@pytest.mark.parametrize("pregunta", [
    "Ahora me interesan las ofertas de Psicología.",
    "Cambiando de tema, quiero construir robots industriales.",
    "¿Qué carreras ofrece la Universidad ICEL?",
    "No quiero modalidad mixta; busco únicamente escolarizada.",
    "Ahora muéstrame las carreras de Arquitectura.",
])
def test_no_conserva_temas_independientes(pregunta):
    assert not es_seguimiento(pregunta)


def test_semantico_cambia_modalidad_sin_perder_programas():
    contexto = crear_contexto()
    contexto["programas_semanticos"] = [526, 338, 185]
    contexto["modalidad"] = "ESCOLARIZADA"
    pregunta = "Ahora muéstrame las opciones mixtas."
    assert es_seguimiento(pregunta)
    nuevo = actualizar_contexto(contexto, {
        "pregunta": pregunta,
        "institucion": None,
        "programa": None,
        "modalidad": "MIXTA",
    })
    assert nuevo["programas_semanticos"] == [526, 338, 185]
    assert nuevo["modalidad"] == "MIXTA"
    assert contexto["modalidad"] == "ESCOLARIZADA"


def test_referencia_a_licenciatura_conserva_carrera_y_universidad():
    contexto = crear_contexto()
    contexto["programa"] = {"id_programa": 338, "nombre": "EN INGENIERÍA EN ANIMACIÓN Y VIDEOJUEGOS"}
    contexto["institucion"] = {"id_institucion": 20, "nombre": "UNIVERSIDAD PANAMERICANA"}
    pregunta = "¿Esa licenciatura se puede cursar en modalidad mixta?"
    assert es_seguimiento_estructurado(pregunta, contexto)
    nuevo = actualizar_contexto(contexto, {
        "pregunta": pregunta,
        "institucion": None,
        "programa": None,
        "modalidad": "MIXTA",
    })
    assert nuevo["institucion"] == contexto["institucion"]
    assert nuevo["programa"] == contexto["programa"]
    assert nuevo["modalidad"] == "MIXTA"


def test_siguiente_institucion_conserva_institucion():
    contexto = crear_contexto()
    contexto["institucion"] = {"id_institucion": 1, "nombre": "UNIVERSIDAD ICEL"}
    pregunta = "Ahora muéstrame las opciones mixtas"
    assert es_seguimiento_estructurado(pregunta, contexto)
    nuevo = actualizar_contexto(contexto, {
        "pregunta": pregunta,
        "institucion": None,
        "programa": None,
        "modalidad": "MIXTA",
    })
    assert nuevo["institucion"] == contexto["institucion"]
    assert nuevo["modalidad"] == "MIXTA"


def test_nueva_pregunta_reinicia_la_memoria():
    contexto = crear_contexto()
    contexto["programas_semanticos"] = [526, 338]
    contexto["modalidad"] = "MIXTA"
    nuevo_programa = {"id_programa": 10, "nombre": "EN PSICOLOGÍA"}
    nuevo = actualizar_contexto(contexto, {
        "pregunta": "Ahora me interesan las ofertas de Psicología.",
        "institucion": None,
        "programa": nuevo_programa,
        "modalidad": None,
    })
    assert nuevo["programas_semanticos"] == []
    assert nuevo["modalidad"] is None
    assert nuevo["programa"] == nuevo_programa


def test_contexto_semantico_no_es_contexto_estructurado():
    contexto = crear_contexto()
    contexto["programas_semanticos"] = [526]
    assert not es_seguimiento_estructurado("Ahora muéstrame las opciones mixtas", contexto)


def test_modalidad_sin_carrera_previa_no_es_seguimiento_estructurado():
    contexto = crear_contexto()
    contexto["modalidad"] = "NO ESCOLARIZADA"
    assert not es_seguimiento_estructurado("¿Esa licenciatura es mixta?", contexto)
