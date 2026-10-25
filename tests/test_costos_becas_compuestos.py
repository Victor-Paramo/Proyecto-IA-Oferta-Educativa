"""Regresión de consultas compuestas sobre datos económicos no disponibles."""
from motor_ia.interaccion_general import detectar_interaccion_general


def test_costos_y_becas_compuestos():
    respuesta = detectar_interaccion_general(
        "¿Cuánto cuesta estudiar esa carrera y hay becas disponibles?"
    )
    assert respuesta is not None and respuesta["cerrar"] is False
    assert "costos" in respuesta["mensaje"]
    assert "becas" in respuesta["mensaje"]


def test_colegiatura_y_apoyos_economicos():
    respuesta = detectar_interaccion_general(
        "¿Cuál es el costo de colegiatura y qué apoyos económicos existen?"
    )
    assert "costos" in respuesta["mensaje"]
    assert "becas" in respuesta["mensaje"]


def test_costo_individual_no_menciona_becas():
    respuesta = detectar_interaccion_general("¿Cuánto cuesta estudiar Derecho?")
    assert respuesta is not None
    assert "costos" in respuesta["mensaje"]
    assert "becas" not in respuesta["mensaje"]


def test_becas_individuales():
    respuesta = detectar_interaccion_general("¿Qué becas hay para Psicología?")
    assert respuesta is not None
    assert "becas" in respuesta["mensaje"]
    assert "colegiaturas" not in respuesta["mensaje"]


def test_busqueda_academica_no_interceptada():
    assert detectar_interaccion_general(
        "¿Dónde puedo estudiar Psicología en modalidad mixta?"
    ) is None


def test_seguimiento_academico_no_interceptado():
    assert detectar_interaccion_general("¿Y cuáles son escolarizadas?") is None


def test_vigencia_no_regresion():
    respuesta = detectar_interaccion_general(
        "¿Las licenciaturas siguen vigentes actualmente?"
    )
    assert "2021" in respuesta["mensaje"]


def test_despedida_no_regresion():
    respuesta = detectar_interaccion_general("Gracias por la información. Hasta pronto.")
    assert respuesta["cerrar"] is True
