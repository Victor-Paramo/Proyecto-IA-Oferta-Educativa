"""Regresiones de contexto para la evaluación independiente de etapa 4."""
import pytest

from motor_ia.contexto import (
    crear_contexto,
    es_seguimiento,
    es_seguimiento_estructurado,
    actualizar_contexto,
)
from motor_ia.interpretar_modalidades import analizar_modalidades, ajustar_interpretacion


@pytest.mark.parametrize("pregunta", [
    "¿Y si prefiero una modalidad mixta?",
    "¿Y si prefiero modalidad escolarizada?",
    "¿Y si quiero clases en línea?",
    "¿Qué opciones de esa institución son presenciales?",
    "¿Cuáles de esa universidad tienen modalidad mixta?",
    "¿Esa licenciatura se puede cursar en modalidad mixta?",
    "Ahora muéstrame las opciones mixtas.",
    "¿Cuáles de esas ofertas se pueden cursar a distancia?",
])
def test_reconoce_seguimientos(pregunta):
    assert es_seguimiento(pregunta)


@pytest.mark.parametrize("pregunta", [
    "¿Y si prefiero estudiar Psicología?",
    "Dejemos esa universidad; ¿qué licenciaturas aparecen en el Instituto SAE?",
    "Cambiemos de tema, quiero construir robots industriales.",
    "¿Qué carreras ofrece la Universidad ICEL?",
    "Ahora muéstrame las carreras de Arquitectura.",
    "No quiero modalidad mixta; busco únicamente escolarizada.",
])
def test_no_confunde_temas_nuevos(pregunta):
    assert not es_seguimiento(pregunta)


def interpretar_filtro(pregunta):
    base = {
        "pregunta": pregunta,
        "intencion": "filtrar_modalidad",
        "confianza": 0.4,
        "institucion": None,
        "programa": None,
        "modalidad": None,
    }
    return ajustar_interpretacion(base, analizar_modalidades(pregunta))


def test_uvm_prefiere_mixta_sin_perder_institucion():
    contexto = crear_contexto()
    uvm = {"id_institucion": 10, "nombre": "UNIVERSIDAD DEL VALLE DE MÉXICO"}
    contexto["institucion"] = uvm
    contexto["modalidad"] = "NO ESCOLARIZADA"
    pregunta = "¿Y si prefiero una modalidad mixta?"
    assert es_seguimiento_estructurado(pregunta, contexto)
    actualizado = actualizar_contexto(contexto, interpretar_filtro(pregunta))
    assert actualizado["institucion"] == uvm
    assert actualizado["modalidad"] == "MIXTA"
    assert actualizado["programa"] is None


def test_sae_referencia_esa_institucion():
    contexto = crear_contexto()
    sae = {"id_institucion": 20, "nombre": "INSTITUTO SAE"}
    contexto["institucion"] = sae
    pregunta = "¿Qué opciones de esa institución son presenciales?"
    assert es_seguimiento_estructurado(pregunta, contexto)
    actualizado = actualizar_contexto(contexto, interpretar_filtro(pregunta))
    assert actualizado["institucion"] == sae
    assert actualizado["modalidad"] == "ESCOLARIZADA"


def test_cambio_institucion_descarta_modalidad_previa():
    contexto = crear_contexto()
    contexto["institucion"] = {"id_institucion": 10, "nombre": "UVM"}
    contexto["modalidad"] = "NO ESCOLARIZADA"
    pregunta = "Dejemos esa universidad; ¿qué licenciaturas aparecen en el Instituto SAE?"
    interpretacion = {
        "pregunta": pregunta,
        "institucion": {"id_institucion": 20, "nombre": "INSTITUTO SAE"},
        "programa": None,
        "modalidad": None,
    }
    actualizado = actualizar_contexto(contexto, interpretacion)
    assert actualizado["institucion"]["nombre"] == "INSTITUTO SAE"
    assert actualizado["modalidad"] is None


def test_lista_semantica_sigue_filtrando():
    contexto = crear_contexto()
    contexto["programas_semanticos"] = [101, 102]
    pregunta = "¿Y cuáles de esas opciones son mixtas?"
    assert not es_seguimiento_estructurado(pregunta, contexto)
    actualizado = actualizar_contexto(contexto, interpretar_filtro(pregunta))
    assert actualizado["programas_semanticos"] == [101, 102]
    assert actualizado["modalidad"] == "MIXTA"


def test_nueva_consulta_no_hereda_programas_semanticos():
    contexto = crear_contexto()
    contexto["programas_semanticos"] = [101, 102]
    pregunta = "¿Qué carreras ofrece la Universidad ICEL?"
    interpretacion = {
        "pregunta": pregunta,
        "institucion": {"id_institucion": 30, "nombre": "UNIVERSIDAD ICEL"},
        "programa": None,
        "modalidad": None,
    }
    actualizado = actualizar_contexto(contexto, interpretacion)
    assert actualizado["programas_semanticos"] == []
    assert actualizado["institucion"]["nombre"] == "UNIVERSIDAD ICEL"
