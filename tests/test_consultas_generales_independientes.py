"""Regresiones de becas, vigencia y despedidas (sin PostgreSQL ni MiniLM)."""
import pytest
from motor_ia.interaccion_general import detectar_interaccion_general


@pytest.mark.parametrize("pregunta", [
    "¿Qué becas puedo solicitar para estudiar Contaduría?",
    "¿La Universidad ICEL tiene becas?",
    "¿Existen apoyos económicos para estudiar Derecho?",
    "¿Dónde consulto las convocatorias de becas para Psicología?",
    "¿Qué financiamiento educativo puedo solicitar?",
])
def test_becas_fuera_de_alcance(pregunta):
    respuesta = detectar_interaccion_general(pregunta)
    assert respuesta is not None
    assert respuesta["cerrar"] is False
    assert "becas" in respuesta["mensaje"].lower()
    assert "no tengo información" in respuesta["mensaje"].lower()


@pytest.mark.parametrize("pregunta", [
    "¿Las carreras que muestras siguen vigentes este año?",
    "¿Es vigente Psicología en el Instituto SAE?",
    "¿Qué licenciaturas ofrece actualmente la Universidad ICEL?",
    "¿Las ofertas educativas están actualizadas?",
    "¿La Universidad ICEL sigue ofreciendo Psicología?",
    "¿Las carreras todavía se imparten?",
    "¿Qué programas se ofrecen en 2026?",
    "¿De qué año son los datos?",
])
def test_vigencia_historica(pregunta):
    respuesta = detectar_interaccion_general(pregunta)
    assert respuesta is not None, pregunta
    assert respuesta["cerrar"] is False
    assert "2021" in respuesta["mensaje"]
    assert "no puedo verificar" in respuesta["mensaje"].lower()


@pytest.mark.parametrize("pregunta", [
    "Gracias por la orientación; nos vemos pronto.",
    "Gracias, nos vemos pronto.",
    "Muchas gracias, hasta luego.",
    "Nos vemos pronto.",
    "Gracias por todo. Hasta luego.",
])
def test_despedidas_compuestas(pregunta):
    respuesta = detectar_interaccion_general(pregunta)
    assert respuesta is not None, pregunta
    assert respuesta["cerrar"] is True


@pytest.mark.parametrize("pregunta", [
    "Gracias, ¿y cuáles son mixtas?",
    "Buenas tardes, ¿qué universidades ofrecen Psicología en modalidad mixta?",
    "Quiero desarrollar mundos virtuales para videojuegos",
    "¿Qué programas ofrece la Universidad ICEL?",
    "¿Qué modalidades hay para Ciencia de Datos?",
    "Quiero aprender sobre finanzas y mercados",
    "¿Dónde estudiar Historia?",
    "Me gustaría consultar las opciones escolarizadas",
    "¿Qué escuelas de diseño hay en CDMX?",
])
def test_consultas_academicas_siguen_ruta_normal(pregunta):
    assert detectar_interaccion_general(pregunta) is None


def test_no_inventa_importes_becas():
    respuesta = detectar_interaccion_general("¿Cuánto dinero me da una beca para Contaduría?")
    assert respuesta is not None
    assert "No tengo información" in respuesta["mensaje"]
    assert "no puedo" in respuesta["mensaje"].lower()
