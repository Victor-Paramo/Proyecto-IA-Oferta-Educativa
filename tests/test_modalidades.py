"""Pruebas aisladas: no necesitan PostgreSQL ni MiniLM."""
import unittest

from motor_ia.interpretar_modalidades import (
    analizar_modalidades, ajustar_interpretacion, mensaje_aclaracion_modalidad,
)


class TestModalidades(unittest.TestCase):
    def comprobar(self, pregunta, esperada, excluidas=()):
        analisis = analizar_modalidades(pregunta)
        self.assertEqual(analisis['modalidad'], esperada, pregunta)
        self.assertEqual(set(analisis['excluidas']), set(excluidas), pregunta)
        return analisis

    def test_desde_casa(self):
        self.comprobar('Busco carreras que pueda cursar totalmente desde casa.', 'NO ESCOLARIZADA')

    def test_en_linea(self):
        self.comprobar('Muéstrame licenciaturas en línea.', 'NO ESCOLARIZADA')

    def test_no_escolarizada_literal(self):
        self.comprobar('¿Qué hay en modalidad no escolarizada?', 'NO ESCOLARIZADA')

    def test_negacion_y_seleccion(self):
        self.comprobar('No quiero modalidad mixta; busco únicamente escolarizada.', 'ESCOLARIZADA', ('MIXTA',))

    def test_solo_negacion_pide_aclaracion(self):
        a = self.comprobar('No quiero modalidad mixta.', None, ('MIXTA',))
        self.assertIn('¿Prefieres', mensaje_aclaracion_modalidad(a))

    def test_negacion_no_escolarizada_con_eleccion(self):
        self.comprobar('No quiero la modalidad no escolarizada, prefiero presencial.', 'ESCOLARIZADA', ('NO ESCOLARIZADA',))

    def test_modalidad_presencial(self):
        self.comprobar('¿Cuáles tienen clases presenciales?', 'ESCOLARIZADA')

    def test_modalidad_semipresencial(self):
        self.comprobar('¿Y cuáles son semipresenciales?', 'MIXTA')

    def test_mixta_sin_negacion(self):
        self.comprobar('¿No hay carreras mixtas?', 'MIXTA')

    def test_modalidades_multiples_piden_aclaracion(self):
        a = self.comprobar('Quiero carreras mixtas y escolarizadas.', None)
        self.assertTrue(a['ambigua'])

    def test_sin_modalidad(self):
        self.comprobar('¿Qué carreras ofrece la Universidad ICEL?', None)

    def test_cambio_de_intencion_sin_entidades(self):
        a = analizar_modalidades('Quiero estudiar totalmente desde casa.')
        interpretacion = dict(intencion='buscar_programa', programa=None, institucion=None, modalidad=None)
        ajustada = ajustar_interpretacion(interpretacion, a)
        self.assertEqual(ajustada['intencion'], 'filtrar_modalidad')
        self.assertEqual(ajustada['modalidad'], 'NO ESCOLARIZADA')

    def test_prioriza_entidad_y_modalidad(self):
        a = analizar_modalidades('¿Psicología en modalidad mixta?')
        programa = {'id_programa': 1, 'nombre': 'EN PSICOLOGÍA'}
        interpretacion = dict(intencion='buscar_programa', programa=programa, institucion=None, modalidad=None)
        ajustada = ajustar_interpretacion(interpretacion, a)
        self.assertIs(ajustada['programa'], programa)
        self.assertEqual(ajustada['modalidad'], 'MIXTA')
        self.assertEqual(ajustada['intencion'], 'buscar_programa')

    def test_interes_y_modalidad(self):
        a = analizar_modalidades('Quiero diseñar videojuegos en modalidad mixta')
        interpretacion = dict(intencion='buscar_institucion', programa=None, institucion=None, modalidad=None)
        ajustada = ajustar_interpretacion(interpretacion, a, tiene_tema=True)
        self.assertEqual(ajustada['intencion'], 'explorar_area')
        self.assertEqual(ajustada['modalidad'], 'MIXTA')


if __name__ == '__main__':
    unittest.main()
