"""Regresión del ciclo de vida del motor desde la interfaz de escritorio.

La despedida finaliza la conversación activa sin destruir la conexión que
permite iniciar una conversación nueva. No requiere Tk ni PostgreSQL.
"""
import ast
import queue
import sys
import threading
import types
from pathlib import Path
from unittest.mock import patch


RUTA_INTERFAZ = Path(__file__).resolve().parents[1] / "interfaz_escritorio.py"


def cargar_trabajador():
    arbol = ast.parse(RUTA_INTERFAZ.read_text(encoding="utf-8"))
    clase = next(n for n in arbol.body if isinstance(n, ast.ClassDef) and n.name == "InterfazEducativa")
    funcion = next(n for n in clase.body if isinstance(n, ast.FunctionDef) and n.name == "_trabajar")
    codigo = compile(ast.Module(body=[funcion], type_ignores=[]), str(RUTA_INTERFAZ), "exec")
    return codigo


def test_despedida_permite_nueva_conversacion():
    creados = []

    class MotorFalso:
        def __init__(self, contrasena):
            self.contexto = {"programa": "Psicología"}
            self.opciones_pendientes = {"tema": "salud"}
            self.cerrado = False
            self._pag_busqueda = 1
            self._pag_ofertas = [{"programa": "Psicolog?a"}]
            self._pag_contexto = {"modalidad": "MIXTA"}
            creados.append(self)

        def procesar(self, pregunta):
            if pregunta == "adios":
                return {"mensaje": "Hasta luego", "cerrar": True}
            return {"mensaje": "Respuesta de prueba", "cerrar": False}

        def cerrar(self):
            self.cerrado = True

    contexto_falso = types.ModuleType("motor_ia.contexto")
    contexto_falso.crear_contexto = lambda: {"programa": None}
    paquete_falso = types.ModuleType("motor_ia")
    paquete_falso.__path__ = []
    espacio = {"MotorEducativo": MotorFalso}
    exec(cargar_trabajador(), espacio)
    trabajador = espacio["_trabajar"]
    gui = types.SimpleNamespace(motor=None, eventos=queue.Queue(), solicitudes=queue.Queue())

    with patch.dict(sys.modules, {"motor_ia": paquete_falso, "motor_ia.contexto": contexto_falso}):
        hilo = threading.Thread(target=trabajador, args=(gui, "credencial-falsa"), daemon=True)
        hilo.start()
        try:
            assert gui.eventos.get(timeout=2) == ("listo", None)
            gui.solicitudes.put(("pregunta", "adios"))
            tipo, respuesta = gui.eventos.get(timeout=2)
            assert tipo == "respuesta" and respuesta["cerrar"] is True
            assert hilo.is_alive(), "La despedida no debe terminar el hilo del motor"
            assert not gui.motor.cerrado

            gui.solicitudes.put(("nuevo", None))
            assert gui.eventos.get(timeout=2) == ("nuevo", None)
            assert gui.motor.contexto == {"programa": None}
            assert gui.motor.opciones_pendientes is None
            assert gui.motor._pag_busqueda == 2
            assert gui.motor._pag_ofertas is None
            assert gui.motor._pag_contexto is None

            gui.solicitudes.put(("pregunta", "medicina"))
            tipo, respuesta = gui.eventos.get(timeout=2)
            assert tipo == "respuesta" and respuesta["cerrar"] is False
            assert len(creados) == 1, "El modelo no debe recargarse al empezar otro chat"
        finally:
            gui.solicitudes.put(("cerrar", None))
            hilo.join(timeout=2)
        assert not hilo.is_alive()
        assert gui.motor.cerrado
        assert gui.eventos.get(timeout=2) == ("finalizado", None)
