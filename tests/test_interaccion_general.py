"""Pruebas de interacciones generales sin PostgreSQL ni MiniLM."""
import pytest

from motor_ia.interaccion_general import detectar_interaccion_general


@pytest.mark.parametrize("pregunta", [
    "Hola", "Buenas", "Buenos días", "¡Hola! ¿Cómo estás?", "Qué tal",
])
def test_saludos(pregunta):
    resultado = detectar_interaccion_general(pregunta)
    assert resultado is not None
    assert resultado["cerrar"] is False
    assert "Hola" in resultado["mensaje"]


@pytest.mark.parametrize("pregunta", [
    "Muchas gracias, me ayudaste.", "Gracias", "Gracias por tu ayuda",
])
def test_agradecimientos(pregunta):
    resultado = detectar_interaccion_general(pregunta)
    assert resultado is not None
    assert "Con gusto" in resultado["mensaje"]
    assert resultado["cerrar"] is False


@pytest.mark.parametrize("pregunta", [
    "Adiós, hablamos después.", "Nos vemos", "Hasta luego",
])
def test_despedidas(pregunta):
    resultado = detectar_interaccion_general(pregunta)
    assert resultado is not None
    assert "Hasta luego" in resultado["mensaje"]
    assert resultado["cerrar"] is True


@pytest.mark.parametrize("pregunta", [
    "¿Cuánto cuesta la colegiatura de las universidades?",
    "¿Cuánto cuesta estudiar Psicología en la Universidad ICEL?",
    "¿Tienes información de colegiaturas?",
    "¿Cuál es el precio de inscripción?",
])
def test_sin_datos_costos(pregunta):
    resultado = detectar_interaccion_general(pregunta)
    assert resultado is not None
    assert "No tengo información" in resultado["mensaje"]
    assert resultado["cerrar"] is False


@pytest.mark.parametrize("pregunta", [
    "Buenas, quisiera orientación para elegir una licenciatura.",
    "Quiero orientación vocacional", "No sé qué estudiar",
])
def test_orientacion_general(pregunta):
    resultado = detectar_interaccion_general(pregunta)
    assert resultado is not None
    assert "qué materias" in resultado["mensaje"]


@pytest.mark.parametrize("pregunta", [
    "¿Qué puedes hacer?", "¿En qué me puedes ayudar?", "Ayuda",
])
def test_capacidades(pregunta):
    resultado = detectar_interaccion_general(pregunta)
    assert resultado is not None
    assert "modalidades" in resultado["mensaje"]


@pytest.mark.parametrize("pregunta", [
    "Hola, ¿dónde puedo estudiar Psicología?",
    "Gracias, ¿y cuáles son mixtas?",
    "Buenas, quiero estudiar videojuegos",
    "¿Qué carreras ofrece la Universidad ICEL?",
    "¿Y cuáles son mixtas?",
    "Me gustan las matemáticas y resolver problemas de lógica.",
    "Sí", "No gracias", "Quiero pronosticar huracanes",
    "¿La Universidad Panamericana ofrece Ingeniería en Animación y Videojuegos?",
])
def test_no_interrumpe_consultas_y_confirmaciones(pregunta):
    assert detectar_interaccion_general(pregunta) is None
