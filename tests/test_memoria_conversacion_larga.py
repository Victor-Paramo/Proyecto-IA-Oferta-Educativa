"""Regresiones de seguimiento detectadas en conversación de diez turnos."""

from motor_ia.contexto import crear_contexto, es_seguimiento, actualizar_contexto
from app import resolver_institucion_mencionada, conservar_seguimiento_academico


def _interpretacion(texto, modalidad=None, institucion=None, programa=None):
    return {"pregunta": texto, "modalidad": modalidad,
            "institucion": institucion, "programa": programa,
            "intencion": "filtrar_modalidad", "confianza": 0.5}


def test_retorno_a_mixta_tras_cero_resultados():
    assert es_seguimiento("¿Y hay alguna que pueda estudiar en modalidad mixta?")
    institucion = {"id_institucion": 1, "nombre": "UNIVERSIDAD LA SALLE"}
    previo = crear_contexto()
    previo.update(institucion=institucion, programas_semanticos=[51])
    previo = actualizar_contexto(previo, _interpretacion(
        "¿Cuáles de esas opciones son escolarizadas?", "ESCOLARIZADA"))
    nuevo = actualizar_contexto(previo, _interpretacion(
        "¿Y hay alguna que pueda estudiar en modalidad mixta?", "MIXTA"))
    assert nuevo["programas_semanticos"] == [51]
    assert nuevo["institucion"] == institucion
    assert nuevo["modalidad"] == "MIXTA"


def test_psicologia_mixta_conserva_carrera():
    previo = crear_contexto()
    previo["programa"] = {"id_programa": 10, "nombre": "PSICOLOGÍA"}
    nuevo = actualizar_contexto(previo, _interpretacion(
        "¿Qué opciones hay en modalidad mixta?", "MIXTA"))
    assert nuevo["programa"] == previo["programa"]
    assert nuevo["modalidad"] == "MIXTA"


def test_institucion_nueva_con_esa_carrera():
    previo = crear_contexto()
    previo["programa"] = {"id_programa": 10, "nombre": "PSICOLOGÍA"}
    previo["modalidad"] = "MIXTA"
    uvm = {"id_institucion": 20, "nombre": "UNIVERSIDAD DEL VALLE DE MÉXICO"}
    nuevo = actualizar_contexto(previo, _interpretacion(
        "¿La Universidad del Valle de México ofrece esa carrera?", institucion=uvm))
    assert nuevo["programa"] == previo["programa"]
    assert nuevo["institucion"] == uvm
    assert nuevo["modalidad"] == "MIXTA"


def test_seguimiento_de_planteles():
    previo = crear_contexto()
    previo["institucion"] = {"id_institucion": 20, "nombre": "UVM"}
    previo["programa"] = {"id_programa": 10, "nombre": "PSICOLOGÍA"}
    pregunta = "¿Y en cuáles de sus planteles aparece registrada?"
    assert es_seguimiento(pregunta)
    assert actualizar_contexto(previo, _interpretacion(pregunta))["programa"] == previo["programa"]


def test_itam_es_catalogo_no_institucion_inventada():
    registro = {"id_institucion": 4, "nombre": "INSTITUTO TECNOLÓGICO AUTÓNOMO DE MÉXICO"}
    assert resolver_institucion_mencionada(
        "Me interesan las telecomunicaciones en el ITAM", None, [registro]
    ) == registro


def test_no_contaminar_nuevo_interes():
    contexto = crear_contexto()
    contexto["institucion"] = {"id_institucion": 4, "nombre": "ITAM"}
    interpretacion = _interpretacion("Ahora me interesan telecomunicaciones en el ITAM")
    assert not conservar_seguimiento_academico(
        interpretacion["pregunta"], interpretacion, contexto
    )


def test_no_mantener_al_cambiar_tema():
    previo = crear_contexto()
    previo["institucion"] = {"id_institucion": 4, "nombre": "ITAM"}
    nuevo = actualizar_contexto(previo, _interpretacion(
        "Olvidemos esa universidad. Quiero estudiar Psicología.",
        programa={"id_programa": 10, "nombre": "PSICOLOGÍA"}))
    assert nuevo["institucion"] is None
    assert nuevo["programa"]["nombre"] == "PSICOLOGÍA"
