"""Pruebas unitarias sin requerir conexión a PostgreSQL ni descargar MiniLM."""
import unittest
from motor_ia.afinidades_academicas import buscar_afinidades
from motor_ia.generador_respuestas import (
    respuesta_sin_cobertura, respuesta_afinidades,
    respuesta_programas, respuesta_ofertas,
)

PROGRAMAS_PRUEBA = [
    (1, 'EN EDUCACIÓN FÍSICA Y DEPORTES'),
    (2, 'EN FÍSICA'),
    (3, 'EN MATEMÁTICAS'),
    (4, 'EN GASTRONOMÍA INTERNACIONAL'),
    (5, 'EN INGENIERÍA MECÁNICA'),
    (6, 'EN BIOLOGÍA'),
    (7, 'EN GEOLOGÍA'),
    (8, 'EN HISTORIA DEL ARTE'),
    (9, 'EN ANTROPOLOGÍA SOCIAL'),
    (10, 'EN INGENIERÍA FÍSICA'),
]


def oferta(nombre, modalidad='MIXTA'):
    return {
        'programa': nombre,
        'institucion': 'UNIVERSIDAD DE PRUEBA',
        'modalidad': modalidad,
        'plantel': None,
    }


class TestAfinidades(unittest.TestCase):
    def test_meteorologia_omite_irrelevantes(self):
        resultados = buscar_afinidades(['meteorologia'], PROGRAMAS_PRUEBA)
        ids = {r['id_programa'] for r in resultados}
        self.assertEqual(ids, {2, 3, 10})
        self.assertNotIn(1, ids)  # Educación Física != Física.
        self.assertNotIn(4, ids)  # Gastronomía nunca es afín en este caso.

    def test_aeroespacial_no_inventa_programas(self):
        resultados = buscar_afinidades(['aeroespacial'], PROGRAMAS_PRUEBA)
        self.assertIn(5, {r['id_programa'] for r in resultados})
        self.assertNotIn(4, {r['id_programa'] for r in resultados})

    def test_paleontologia_usa_titulos_realmente_presentes(self):
        resultados = buscar_afinidades(['paleontologia'], PROGRAMAS_PRUEBA)
        self.assertEqual({r['id_programa'] for r in resultados}, {6, 7})

    def test_areas_desconocidas_no_muestran_opciones(self):
        self.assertEqual(buscar_afinidades(['musica'], PROGRAMAS_PRUEBA), [])

    def test_respuestas_explican_limites(self):
        mensaje = respuesta_sin_cobertura(['meteorologia'], True)
        self.assertIn('Meteorología', mensaje)
        self.assertIn('afines', mensaje)
        self.assertIn('abril de 2021', mensaje)
        candidatos = buscar_afinidades(['meteorologia'], PROGRAMAS_PRUEBA)
        ofertas = [{**r, 'ofertas': [oferta(r['nombre'])]} for r in candidatos]
        resultado = respuesta_afinidades(ofertas, ['meteorologia'])
        self.assertIn('Física', resultado)
        self.assertNotIn('GASTRONOMÍA', resultado)
        self.assertIn('NO son carreras especializadas', resultado)

    def test_respuestas_directas_y_seguimiento(self):
        lista = [{
            'programa': 'EN PROGRAMACIÓN DE VIDEOJUEGOS',
            'ofertas': [oferta('EN PROGRAMACIÓN DE VIDEOJUEGOS')]
        }]
        self.assertIn('videojuegos', respuesta_programas(lista, ['videojuegos']))
        contexto = {'institucion': None, 'programa': None, 'modalidad': 'MIXTA'}
        self.assertIn('modalidad mixta', respuesta_ofertas(lista[0]['ofertas'], contexto))


if __name__ == '__main__':
    unittest.main()
