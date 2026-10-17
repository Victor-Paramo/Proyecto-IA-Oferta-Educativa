"""Validaciones preliminares de consultas antes de recuperar ofertas.

No estima la pertinencia de los resultados de MiniLM; esa tarea sigue pendiente.
"""
from motor_ia.entidades import normalizar_texto
from motor_ia.interaccion_general import detectar_interaccion_general


def validar_consulta(interpretacion):
    """Devuelve un mensaje de aclaracion, o None si se puede continuar."""
    texto = normalizar_texto(interpretacion["pregunta"]).strip()
    intencion = interpretacion["intencion"]
    institucion = interpretacion["institucion"]
    programa = interpretacion["programa"]
    modalidad = interpretacion["modalidad"]

    # Mantener el mismo tratamiento si este validador se utiliza por separado.
    interaccion = detectar_interaccion_general(interpretacion["pregunta"])
    if interaccion is not None:
        return interaccion["mensaje"]

    # Consultas sin intereses o criterios suficientes.
    vagas = {
        "quiero estudiar algo",
        "quiero estudiar algo pero todavia no se que",
        "quiero estudiar algo pero no se que",
        "quiero estudiar una carrera pero no se cual",
        "no se que estudiar",
        "no tengo idea de que estudiar",
        "recomiendame una carrera",
        "que puedo estudiar",
    }
    if texto in vagas and not any((institucion, programa, modalidad)):
        return "¿Que actividades te gustan o que temas te interesaria estudiar?"

    # Se predijo una busqueda concreta, pero no se reconocio su entidad.
    if intencion == "buscar_programa" and programa is None and institucion is None:
        return ("No pude identificar esa carrera entre los nombres del catalogo "
                "consultado. ¿Puedes indicar otro nombre o describir el area que te interesa?")

    if intencion == "buscar_institucion" and institucion is None and programa is None:
        return ("No pude identificar una institucion del catalogo en tu pregunta. "
                "¿Puedes escribir su nombre completo?")

    if intencion == "filtrar_modalidad" and modalidad is None and not any((institucion, programa)):
        return ("¿Buscas una modalidad escolarizada, mixta o no escolarizada? "
                "Tambien puedes mencionar una carrera o universidad.")

    return None
