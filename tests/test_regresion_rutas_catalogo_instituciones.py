"""Regresión de rutas con catálogos simulados, sin conectar PostgreSQL o MiniLM.

Las consultas se procesan con el clasificador sustituido por una predicción fija.
No se comprueba disponibilidad real, identidad documental ni vigencia de ofertas.
"""
from unittest.mock import Mock

import numpy as np
import pytest

import app


INTENCIONES = ("explorar_area", "buscar_programa", "buscar_institucion", "filtrar_modalidad")
INSTITUCIONES = [
    (1, "UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICO"),
    (2, "INSTITUTO POLITÉCNICO NACIONAL"),
    (3, "UNIVERSIDAD AUTÓNOMA METROPOLITANA"),
    (4, "INSTITUTO TECNOLÓGICO Y DE ESTUDIOS SUPERIORES DE MONTERREY"),
    (5, "INSTITUTO TECNOLÓGICO AUTÓNOMO DE MÉXICO"),
    (6, "UNIVERSIDAD DEL VALLE DE MÉXICO"),
]
PROGRAMAS = [
    (10, "EN DERECHO"),
    (11, "EN IDIOMAS"),
    (12, "EN LENGUAS MODERNAS"),
    (13, "EN INGENIERÍA EN INTELIGENCIA ARTIFICIAL"),
    (14, "EN INGENIERÍA EN CIENCIA DE DATOS"),
    (15, "EN MATEMÁTICAS APLICADAS"),
    (16, "EN PSICOLOGÍA"),
    (17, "EN INGENIERÍA DE SOFTWARE"),
]
OFERTAS = [
    {
        "id_institucion": iid, "id_programa": pid,
        "institucion": nombre, "programa": programa,
        "plantel": f"Plantel de prueba {numero}",
        "modalidad": "MIXTA" if numero % 2 else "ESCOLARIZADA",
    }
    for iid, nombre in INSTITUCIONES
    for numero, (pid, programa) in enumerate(PROGRAMAS * 3)
]


class ModeloFijo:
    def __init__(self, intencion):
        self.intencion = intencion

    def predict(self, textos):
        return np.array([self.intencion] * len(textos))

    def predict_proba(self, textos):
        return np.array([[0.25, 0.25, 0.25, 0.25]] * len(textos))


class CursorSimulado:
    def __init__(self, conexion):
        self.conexion = conexion
        self.description = [(c,) for c in ("institucion", "programa", "plantel", "modalidad")]
        self.filas = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, sql, parametros):
        # Se comprueba que los filtros viajen como parámetros separados del SQL.
        assert "ANY(%s)" in sql
        assert "i.id_institucion = %s" in sql
        ids, modalidad, modalidad_repetida, institucion, institucion_repetida = parametros
        assert modalidad == modalidad_repetida
        assert institucion == institucion_repetida
        self.conexion.consultas.append((sql, parametros))
        filas = [o for o in OFERTAS if o["id_programa"] in ids
                 and (modalidad is None or o["modalidad"] == modalidad)
                 and (institucion is None or o["id_institucion"] == institucion)]
        self.filas = [tuple(o[c[0]] for c in self.description) for o in filas]

    def fetchall(self):
        return self.filas


class ConexionSimulada:
    def __init__(self):
        self.consultas = []

    def cursor(self):
        return CursorSimulado(self)


@pytest.fixture
def motor_factory(monkeypatch):
    def por_institucion(conexion, id_institucion, modalidad=None):
        return [dict(o) for o in OFERTAS if o["id_institucion"] == id_institucion
                and (modalidad is None or o["modalidad"] == modalidad)]

    def por_programa(conexion, id_programa, modalidad=None):
        return [dict(o) for o in OFERTAS if o["id_programa"] == id_programa
                and (modalidad is None or o["modalidad"] == modalidad)]

    institucional = Mock(side_effect=por_institucion)
    programa = Mock(side_effect=por_programa)
    semantica = Mock(side_effect=AssertionError("No corresponde ejecutar MiniLM en este caso"))
    monkeypatch.setattr(app, "buscar_institucion", institucional)
    monkeypatch.setattr(app, "buscar_programa", programa)
    monkeypatch.setattr(app, "buscar_semanticamente", semantica)

    def crear(intencion="explorar_area"):
        # Omitir solo la inicialización de recursos externos.
        motor = app.MotorEducativo.__new__(app.MotorEducativo)
        motor.modelo = ModeloFijo(intencion)
        motor.conexion = ConexionSimulada()
        motor.instituciones = list(INSTITUCIONES)
        motor.programas = list(PROGRAMAS)
        motor.programas_semanticos = list(PROGRAMAS)
        motor.modelo_semantico = object()
        motor.vectores_semanticos = np.zeros((len(PROGRAMAS), 3))
        motor.indice_tematico = app.construir_indice(PROGRAMAS)
        motor.contexto = app.crear_contexto()
        motor.opciones_pendientes = None
        motor._pag_ofertas = None
        motor._pag_contexto = None
        motor._pag_busqueda = 0
        motor._consulta_institucion_prueba = institucional
        motor._consulta_programa_prueba = programa
        motor._consulta_semantica_prueba = semantica
        return motor

    return crear


CONSULTAS_INSTITUCIONALES = [
    ("unam", 1), ("UNAM", 1), ("ipn", 2), ("IPN", 2),
    ("uam", 3), ("UAM", 3), ("tec de monterrey", 4),
    ("Tecnológico de Monterrey", 4), ("ITESM", 4),
    ("itam", 5), ("ITAM", 5), ("uvm", 6),
    ("¿Qué carreras ofrece el ITAM?", 5),
    ("licenciaturas en el itam", 5),
    ("¿Qué carreras ofrece la UNAM en Ciudad de México?", 1),
    ("Muéstrame las licenciaturas de la Universidad Nacional Autónoma de México.", 1),
    ("¿Qué carreras ofrece la UAM?", 3),
    ("¿Qué carreras ofrece el Tecnológico de Monterrey en CDMX?", 4),
] + [(nombre, iid) for iid, nombre in INSTITUCIONES]


@pytest.mark.parametrize("intencion", INTENCIONES)
@pytest.mark.parametrize("pregunta,iid", CONSULTAS_INSTITUCIONALES)
def test_institucion_directa_no_depende_de_la_prediccion(motor_factory, pregunta, iid, intencion):
    motor = motor_factory(intencion)
    resultado = motor.procesar(pregunta)
    motor._consulta_institucion_prueba.assert_called_once_with(
        motor.conexion, id_institucion=iid, modalidad=None)
    assert motor.contexto["institucion"]["id_institucion"] == iid
    assert motor.contexto["programa"] is None
    assert motor._pag_ofertas
    assert {o["institucion"] for o in motor._pag_ofertas} == {dict(INSTITUCIONES)[iid]}
    assert "tema académico" not in resultado["mensaje"]
    assert "Catálogo general" not in resultado["mensaje"]
    motor._consulta_semantica_prueba.assert_not_called()


@pytest.mark.parametrize("pregunta", [
    "que licenciaturas puedo estudiar en la cdmx ?",
    "¿Qué carreras puedo estudiar en CDMX?", "Muéstrame todas las licenciaturas.",
    "¿Cuáles son las carreras disponibles en Ciudad de México?",
    "Lista de carreras", "Catálogo general de licenciaturas", "Todas las licenciaturas",
])
@pytest.mark.parametrize("intencion", INTENCIONES)
def test_catalogo_general_independiente_del_clasificador(motor_factory, pregunta, intencion):
    motor = motor_factory(intencion)
    resultado = motor.procesar(pregunta)
    assert motor._pag_contexto["modo"] == "catalogo_general"
    assert "Catálogo general:" in resultado["mensaje"]
    assert resultado["paginacion"]["total"] == len(PROGRAMAS)
    assert motor._datos_pagina(1)["paginas"] == 2
    motor._consulta_institucion_prueba.assert_not_called()
    motor._consulta_semantica_prueba.assert_not_called()


@pytest.mark.parametrize("pregunta", ["idioma", "idiomas", "IDIOMAS", "¿Idiomas?", "ingeniería", "ingenierías"])
@pytest.mark.parametrize("intencion", INTENCIONES)
def test_categorias_aisladas_no_se_bloquean_por_programa(motor_factory, pregunta, intencion):
    motor = motor_factory(intencion)
    resultado = motor.procesar(pregunta)
    assert "Búsqueda amplia por categoría:" in resultado["mensaje"]
    assert motor._pag_ofertas
    assert motor.contexto["programas_semanticos"]
    assert motor.conexion.consultas
    motor._consulta_semantica_prueba.assert_not_called()


@pytest.mark.parametrize("pregunta", [
    "¿Qué carreras puedo estudiar de Derecho en CDMX?",
    "¿Qué carreras ofrece la UAM?", "¿Qué carreras ofrece la Universidad Desconocida?",
    "¿Qué licenciaturas mixtas hay en CDMX?", "¿Qué carreras puedo estudiar en el ITAM?",
    "¿Qué carreras de idiomas hay en CDMX?", "¿Qué carreras puedo estudiar en inglés?",
    "¿Qué carreras puedo estudiar en Monterrey?", "¿Y cuáles de esas carreras son mixtas?",
])
def test_catalogo_no_absorbe_consultas_con_restricciones(pregunta):
    interpretacion = dict(institucion=None, programa=None, modalidad=None)
    assert not app.es_consulta_catalogo_general(pregunta, interpretacion)


def test_catalogo_textual_no_se_bloquea_por_entidades_espurias(motor_factory, monkeypatch):
    motor = motor_factory("buscar_institucion")
    interpretar = app.interpretar_pregunta
    def espuria(*args):
        valor = interpretar(*args)
        valor["programa"] = {"id_programa": 999, "nombre": "Entidad espuria de prueba"}
        return valor
    monkeypatch.setattr(app, "interpretar_pregunta", espuria)
    resultado = motor.procesar("que licenciaturas puedo estudiar en la cdmx ?")
    assert "Catálogo general:" in resultado["mensaje"]


@pytest.mark.parametrize("pregunta", [
    "ITAM en modalidad mixta", "¿Qué licenciaturas mixtas ofrece el ITAM?",
    "Muéstrame las licenciaturas del ITAM en modalidad mixta",
    "¿Qué carreras ofrece el ITAM en CDMX en modalidad mixta?",
])
def test_institucion_respeta_modalidad(motor_factory, pregunta):
    motor = motor_factory()
    motor.procesar(pregunta)
    motor._consulta_institucion_prueba.assert_called_once_with(
        motor.conexion, id_institucion=5, modalidad="MIXTA")
    assert {o["modalidad"] for o in motor._pag_ofertas} == {"MIXTA"}


def test_sigla_aislada_reemplaza_contexto_anterior(motor_factory):
    motor = motor_factory()
    motor.contexto = {"institucion": {"id_institucion": 5, "nombre": dict(INSTITUCIONES)[5]},
                     "programa": {"id_programa": 10, "nombre": "EN DERECHO"},
                     "modalidad": "MIXTA", "programas_semanticos": [10]}
    motor.procesar("unam")
    assert motor.contexto["institucion"]["id_institucion"] == 1
    assert motor.contexto["programa"] is None
    assert motor.contexto["modalidad"] is None
    assert not motor.contexto["programas_semanticos"]


def test_institucion_preserva_seguimiento_y_paginacion(motor_factory):
    motor = motor_factory()
    primero = motor.procesar("ITAM")
    assert primero["paginacion"]["total"] == 24
    segundo = motor.obtener_pagina({"busqueda": primero["paginacion"]["busqueda"], "pagina": 2})
    assert "Mostrando ofertas 16 a 24 de 24." in segundo["mensaje"]
    motor.procesar("¿Y cuáles son mixtas?")
    assert motor.contexto["institucion"]["id_institucion"] == 5
    assert {o["modalidad"] for o in motor._pag_ofertas} == {"MIXTA"}
    obsoleto = motor.obtener_pagina({"busqueda": primero["paginacion"]["busqueda"], "pagina": 2})
    assert "ya no está activa" in obsoleto["mensaje"]


def test_idiomas_preserva_categoria_en_seguimiento(motor_factory):
    motor = motor_factory()
    motor.procesar("idiomas")
    assert set(motor.contexto["programas_semanticos"]) == {11, 12}
    motor.procesar("¿Y cuáles son mixtas?")
    assert {o["id_programa"] for o in motor._pag_ofertas} <= {11, 12}
    assert {o["modalidad"] for o in motor._pag_ofertas} == {"MIXTA"}


@pytest.mark.parametrize("pregunta", ["ipn", "uam", "tec de monterrey", "unam", "itam"])
def test_alias_ausente_no_inventa_instituciones(motor_factory, pregunta):
    motor = motor_factory()
    motor.instituciones = []
    resultado = motor.procesar(pregunta)
    assert "no encontré esa institución" in resultado["mensaje"]
    motor._consulta_institucion_prueba.assert_not_called()
    assert motor._pag_ofertas is None


@pytest.mark.parametrize("pregunta", ["vitamina", "guam", "unamigos", "tecnología", "tec"])
def test_alias_no_coincide_con_fragmentos(pregunta):
    assert app.identificar_sigla_institucional(pregunta) is None


@pytest.mark.parametrize("pregunta", [
    "¿Cuánto cuesta estudiar en el ITAM?", "¿Qué becas ofrece la UNAM?",
    "Quiero estudiar Derecho en la UNAM", "Me interesa robótica en el IPN",
    "¿Y cuáles de esas opciones del ITAM son mixtas?",
])
def test_nombre_institucional_no_convierte_todo_en_listado(pregunta):
    institucion = app.resolver_institucion_mencionada(pregunta, None, INSTITUCIONES)
    assert not app.es_consulta_institucional_directa(pregunta, institucion)


@pytest.mark.parametrize("como_diccionario", [False, True])
@pytest.mark.parametrize("consulta,iid", [("ipn", 2), ("uam", 3), ("Tec de Monterrey", 4), ("itam", 5)])
def test_alias_con_catalogos_tuplas_o_diccionarios(como_diccionario, consulta, iid):
    catalogo = ([{"id_institucion": i, "nombre": n} for i, n in INSTITUCIONES]
                if como_diccionario else INSTITUCIONES)
    encontrada = app.resolver_institucion_mencionada(consulta, None, catalogo)
    assert encontrada == {"id_institucion": iid, "nombre": dict(INSTITUCIONES)[iid]}


def test_programa_y_ipn_no_incluyen_itam(motor_factory):
    motor = motor_factory("buscar_programa")
    motor.procesar("¿Dónde puedo estudiar Ingeniería en Inteligencia Artificial en el IPN?")
    assert motor.contexto["institucion"]["id_institucion"] == 2
    assert motor.contexto["programa"]["id_programa"] == 13
    assert {o["institucion"] for o in motor._pag_ofertas} == {dict(INSTITUCIONES)[2]}


def test_exploracion_semantica_conserva_institucion(motor_factory, monkeypatch):
    motor = motor_factory()
    candidatos = [{"id_programa": 17, "nombre": dict(PROGRAMAS)[17], "similitud": 0.8}]
    semantica = Mock(return_value=candidatos)
    monkeypatch.setattr(app, "buscar_semanticamente", semantica)
    monkeypatch.setattr(app, "recuperar_ofertas", lambda conexion, cs: [{
        "id_programa": 17, "programa": dict(PROGRAMAS)[17], "similitud": 0.8,
        "ofertas": [dict(o) for o in OFERTAS if o["id_programa"] == 17],
        "total_ofertas": 18, "total_instituciones": 6,
    }])
    salida = motor.procesar("Quiero estudiar algo relacionado con computación en el IPN")
    assert semantica.call_count == 1
    assert dict(INSTITUCIONES)[2] in salida["mensaje"]
    assert dict(INSTITUCIONES)[5] not in salida["mensaje"]
    assert motor.contexto["institucion"]["id_institucion"] == 2


def test_costos_y_becas_no_se_sustituyen_por_carreras(motor_factory):
    motor = motor_factory()
    resultado = motor.procesar("¿Cuánto cuesta estudiar en el ITAM y qué becas ofrece?")
    assert "costos" in resultado["mensaje"] and "becas" in resultado["mensaje"]
    motor._consulta_institucion_prueba.assert_not_called()
