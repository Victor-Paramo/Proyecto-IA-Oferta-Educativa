"""Regresiones: mundos virtuales no es una modalidad de estudio."""
import pytest
from motor_ia.interpretar_modalidades import analizar_modalidades


@pytest.mark.parametrize("pregunta", [
    "Me gustaría desarrollar videojuegos y programar mundos virtuales",
    "Quiero diseñar personajes para mundos virtuales",
    "Me interesa crear experiencias de realidad virtual",
    "Quiero diseñar entornos virtuales para un videojuego",
    "Quiero trabajar con simuladores virtuales",
    "Quiero estudiar videojuegos y crear mundos virtuales",
])
def test_virtual_no_implica_modalidad(pregunta):
    assert analizar_modalidades(pregunta)["modalidad"] is None


@pytest.mark.parametrize("pregunta", [
    "Prefiero clases virtuales",
    "Quiero estudiar en modalidad virtual",
    "Busco cursos virtuales",
    "Quiero estudiar de forma virtual",
    "Prefiero estudiar virtualmente",
    "Quiero estudiar a distancia",
    "Busco una carrera totalmente desde casa",
    "Quiero estudiar videojuegos en clases virtuales",
])
def test_modalidad_virtual_si_es_explicita(pregunta):
    assert analizar_modalidades(pregunta)["modalidad"] == "NO ESCOLARIZADA"


def test_rechazar_modalidad_virtual():
    analisis = analizar_modalidades("No quiero clases virtuales, prefiero presencial")
    assert analisis["modalidad"] == "ESCOLARIZADA"
    assert analisis["excluidas"] == ("NO ESCOLARIZADA",)
