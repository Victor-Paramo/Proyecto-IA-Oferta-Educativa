"""Regresión de siglas institucionales con distintos formatos del catálogo."""

from app import resolver_institucion_mencionada


def test_itam_catalogo_tuplas():
    catalogo = [(12, 'UNIVERSIDAD LA SALLE'), (45, 'INSTITUTO TECNOLÓGICO AUTÓNOMO DE MÉXICO')]
    assert resolver_institucion_mencionada('Telecomunicaciones en el ITAM', None, catalogo) == {
        'id_institucion': 45, 'nombre': 'INSTITUTO TECNOLÓGICO AUTÓNOMO DE MÉXICO'
    }


def test_itam_catalogo_diccionarios():
    catalogo = [{'id_institucion': 45, 'nombre': 'INSTITUTO TECNOLÓGICO AUTÓNOMO DE MÉXICO'}]
    assert resolver_institucion_mencionada('en ITAM', None, catalogo) == catalogo[0]


def test_respeta_entidad_extraida():
    existente = {'id_institucion': 6, 'nombre': 'UNIVERSIDAD LA SALLE'}
    assert resolver_institucion_mencionada('en ITAM', existente, []) == existente


def test_no_inventa_institucion():
    assert resolver_institucion_mencionada('en ITAM', None, [(1, 'OTRA UNIVERSIDAD')]) is None
