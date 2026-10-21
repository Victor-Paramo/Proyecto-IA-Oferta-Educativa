"""Filtro EXPLORATORIO de cobertura temática para la búsqueda semántica.

El vocabulario es una ayuda manual, no una clasificación oficial de la SEP.
Solo se consideran coincidencias directas cuando hay pistas explícitas en el
NOMBRE del programa. Un resultado 'sin_cobertura_directa' NO prueba que el
programa no exista fuera del catálogo ni que no haya disciplinas afines.

Este módulo NO modifica MiniLM ni PostgreSQL y NO asigna las etiquetas humanas
0/1/2. Es un prototipo de abstención previo a la recomendación.
"""
import re
from collections import defaultdict

from motor_ia.descripciones_tematicas import describir_por_nombre, normalizar


# Temas generales y expresiones comunes de estudiantes.
# Estas equivalencias son reglas auxiliares editables, NO datos oficiales SEP.
SENALES = {
    "videojuegos": (
        r"\bvideojuegos?\b", r"\bjuegos? (?:de video|digitales?)\b",
        r"\bmundos? virtuales?\b",
    ),
    "animacion": (
        r"\banimacion\b", r"\banimar\b", r"\bdibujos? animados?\b",
    ),
    "software": (
        r"\bsoftware\b", r"\bprogramar\b", r"\bprogramacion\b",
        r"\baplicaciones? (?:moviles?|informaticas?|para celular)\b",
        r"\binformatica\b", r"\bcomputacion\b",
    ),
    "robotica": (
        r"\brobots?\b", r"\brobotica\b", r"\bmecatronica\b",
        r"\bautomatizaci[oó]n\b", r"\bautomatizados?\b",
    ),
    "electronica": (
        r"\belectronica\b", r"\bcircuitos? (?:electronicos?|electricos?)\b",
        r"\bcomponentes? electronicos?\b",
    ),
    "psicologia": (
        r"\bpsicologia\b", r"\bcomportamiento humano\b",
        r"\bproblemas? emocionales?\b", r"\bsalud mental\b",
    ),
    "derecho": (
        r"\bderecho\b", r"\bderechos? (?:humanos?|de las personas|laborales?)\b",
        r"\bleyes\b", r"\bjuridic[a-z]*\b", r"\babogad[oa]s?\b",
    ),
    "arquitectura": (
        r"\barquitectura\b", r"\bdisen\w* (?:edificios?|casas|viviendas?)\b",
        r"\bespacios? habitables?\b", r"\burbanismo\b",
    ),
    "administracion": (
        r"\badministracion\b", r"\bgestion\w* empresas?\b",
        r"\bgestionar empresas\b", r"\borganizar negocios\b",
        r"\bdirigir empresas\b",
    ),
    "gastronomia": (
        r"\bgastronomia\b", r"\bcocinar\b", r"\bcocina\b", r"\bchef\b",
    ),
    "turismo": (
        r"\bturismo\b", r"\bturistic[a-z]*\b", r"\bhoteleria\b",
        r"\bhoteles\b",
    ),
    "medicina": (
        r"\bmedicina\b", r"\benfermeria\b", r"\bmedic[oa]s?\b",
        r"\batender pacientes\b",
    ),
    "fisica": (
        r"\bfisica\b", r"\bteoria cuantica\b",
    ),
    "matematicas": (
        r"\bmatematic[a-z]*\b", r"\blogica matematica\b",
        r"\bproblemas? de logica\b", r"\brazonamiento logico\b",
        r"\blogica\b",
    ),
    "astronomia": (
        r"\bastronomia\b", r"\bastrofisica\b", r"\bplanetas?\b",
        r"\bexoplanetas?\b", r"\bestrellas?\b", r"\bcosmos\b",
        r"\bespacio exterior\b", r"\bexploracion espacial\b",
    ),
    "aeroespacial": (
        r"\baeroespacial\b", r"\bastronautic[a-z]*\b",
        r"\bcohetes?\b", r"\bnaves? espaciales?\b",
        r"\bingenieria espacial\b", r"\bsondas? espaciales?\b",
        r"\bsatelites?\b", r"\btecnologia espacial\b",
    ),
    "aeronautica": (
        r"\baeronautic[a-z]*\b", r"\baeronaves?\b",
        r"\baviones?\b", r"\baviacion\b",
        r"\bdisen[a-z]* (?:de )?aviones?\b",
    ),
    "meteorologia": (
        r"\bmeteorologia\b", r"\bhuracanes?\b", r"\batmosfera\b",
        r"\bclimatologia\b", r"\bpronostic\w* (?:el )?clima\b",
        r"\bnubes? de tormenta\b", r"\bformacion de nubes\b",
        r"\btormentas? (?:tropicales?|electricas?|en la costa)\b",
        r"\bpronostic\w* (?:nubes?|tormentas?|lluvias?)\b",
        r"\bfenomenos? atmosferic[a-z]*\b",
        r"\btornados?\b", r"\bciclones? tropicales?\b",
    ),
    "arqueologia": (
        r"\barqueologia\b", r"\barqueolog[a-z]*\b",
        r"\bvestigios? arqueologic[a-z]*\b",
    ),
    "paleontologia": (
        r"\bpaleontologia\b", r"\bpaleontolog[a-z]*\b",
        r"\bfosiles\b", r"\bdinosaurios?\b",
    ),
    "geologia": (
        r"\bgeologia\b", r"\bgeolog[oa]s?\b", r"\brocas? y minerales\b",
        r"\bterremotos?\b", r"\bsismos?\b", r"\bvolcanes?\b",
        r"\berupcion(?:es)? volcanicas?\b", r"\bplacas? tectonicas?\b",
        r"\bactividad sismica\b", r"\bgeociencias\b",
        r"\bciencias de la tierra\b",
    ),
    # La referencia a datos debe ser temática: no basta mencionar un número.
    "ciencia_datos": (
        r"\bciencia(?:s)? de datos\b", r"\banalisis de datos\b",
        r"\banalitica de datos\b", r"\bmineria de datos\b",
        r"\bbig data\b", r"\bmodelos? predictivos?\b",
        r"\b(?:usar|utilizar|analizar|estudiar|procesar|trabajar con)\s+datos\b"
        r".{0,110}\b(?:patrones?|predicciones?|predecir|pronosticar)\b",
        r"\bdescubrir patrones?\b.{0,65}\b(?:datos|informacion)\b",
    ),
}

PATRONES = {
    area: tuple(re.compile(p) for p in patrones)
    for area, patrones in SENALES.items()
}


def detectar_temas(pregunta):
    """Identifica temas explícitos; si faltan, prefiere pedir aclaración."""
    texto = normalizar(pregunta)
    return sorted(
        area for area, patrones in PATRONES.items()
        if any(p.search(texto) for p in patrones)
    )


# Si el estudiante menciona una especialidad y una habilidad general, damos
# prioridad a la especialidad. Se conservan ambos temas para diagnóstico.
# Ejemplo: "programar videojuegos" -> videojuegos, no software genérico.
ESPECIALIDADES_PRIORITARIAS = {
    "videojuegos": ("software",),
    "ciencia_datos": ("software",),
}


def priorizar_temas(temas):
    """Evita mezclar una especialidad explícita con un área demasiado general."""
    activos = set(temas)
    for especialidad, generales in ESPECIALIDADES_PRIORITARIAS.items():
        if especialidad in activos:
            activos.difference_update(generales)
    return sorted(activos)


# Expresiones que indican intereses o actividades, no un filtro de modalidad.
# Es una regla auxiliar: no reemplaza al clasificador ni sus puntuaciones.
PATRON_INTERES = re.compile(
    r"^(?:(?:cambiando de tema|cambio de tema|por otro lado)[, ]+)?"
    r"(?:quiero|quisiera|deseo|me interesa|me gustaria|"
    r"me gustan|me encanta|me llama la atencion|me apasiona|"
    r"busco aprender)\b"
)


def es_exploracion_tematica(interpretacion):
    """Rescata intereses claros clasificados erróneamente como modalidad.

    Respeta las entidades explícitas y las modalidades reconocidas para no
    interrumpir búsquedas SQL tradicionales ni preguntas de seguimiento.
    """
    if interpretacion["intencion"] == "explorar_area":
        return True

    # El clasificador puede confundir una expresión vocacional con cualquiera
    # de las tres intenciones estructuradas. Solo recuperamos la ruta temática
    # si realmente existe una señal de interés Y no hay filtros explícitos.
    if interpretacion["intencion"] not in (
        "filtrar_modalidad", "buscar_programa", "buscar_institucion"
    ):
        return False

    if any(interpretacion.get(clave) is not None
           for clave in ("institucion", "programa", "modalidad")):
        return False

    pregunta = interpretacion["pregunta"]
    return bool(PATRON_INTERES.search(normalizar(pregunta))) and bool(
        detectar_temas(pregunta)
    )


# Las etiquetas auxiliares heredadas agrupan astronomía con aeroespacial
# y arqueología con paleontología. Para la COBERTURA DIRECTA separamos
# esas especialidades usando únicamente palabras presentes en el título.
PISTAS_TITULO = {
    "astronomia": (r"\bastronomia\b", r"\bastrofisica\b"),
    "aeroespacial": (
        r"\baeroespacial\b", r"\bastronautic[a-z]*\b",
        r"\bingenieria espacial\b", r"\bingenieria de satelites\b",
        r"\bcohetes?\b", r"\bnaves? espaciales?\b",
    ),
    "aeronautica": (
        r"\baeronautic[a-z]*\b", r"\bingenieria en aeronaves\b",
    ),
    "arqueologia": (r"\barqueologia\b", r"\barqueolog[a-z]*\b"),
    "paleontologia": (r"\bpaleontologia\b", r"\bpaleontolog[a-z]*\b"),
}
PISTAS_TITULO = {
    area: tuple(re.compile(patron) for patron in patrones)
    for area, patrones in PISTAS_TITULO.items()
}


def construir_indice(programas):
    """Recibe (id_programa, nombre) y detecta pistas explícitas del título."""
    indice = defaultdict(list)
    for id_programa, nombre in programas:
        titulo = normalizar(nombre)
        _, etiquetas = describir_por_nombre(nombre)
        areas = set(etiquetas)

        especialidades = {
            area for area, patrones in PISTAS_TITULO.items()
            if any(p.search(titulo) for p in patrones)
        }
        # Estas áreas requieren una pista explícita en el título: una carrera
        # de Astronomía no es equivalente a Aeronáutica o Ingeniería Espacial.
        # Tampoco se considera Arqueología equivalente a Paleontología.
        for especialidad in PISTAS_TITULO:
            areas.discard(especialidad)
        areas.update(especialidades)

        for area in sorted(areas):
            indice[area].append((int(id_programa), nombre))
    return dict(indice)


def comprobar_cobertura(pregunta, indice):
    """Describe si existen programas con pistas explícitas del tema preguntado.

    Estados:
      aclaracion: no se pudo reconocer un tema específico
      sin_cobertura_directa: se reconoció, sin títulos directos en el catálogo
      cobertura_directa: existen títulos con pistas del área indicada
    """
    temas = detectar_temas(pregunta)
    temas_prioritarios = priorizar_temas(temas)
    if not temas:
        return {
            "estado": "aclaracion", "temas": [], "temas_prioritarios": [],
            "ids_validos": set(),
            "mensaje": (
                "No reconocí un tema académico específico con mis reglas "
                "actuales. ¿Podrías describir tus intereses con otras palabras "
                "o indicar el área que te interesa?"
            ),
        }

    temas_presentes = [area for area in temas_prioritarios if indice.get(area)]
    temas_ausentes = [area for area in temas_prioritarios if not indice.get(area)]
    ids = {
        id_programa
        for area in temas_presentes
        for id_programa, _ in indice.get(area, ())
    }
    if not ids:
        return {
            "estado": "sin_cobertura_directa", "temas": temas,
            "temas_prioritarios": temas_prioritarios,
            "temas_sin_cobertura": temas_ausentes,
            "ids_validos": set(),
            "mensaje": (
                "No identifiqué carreras cuyo nombre indique directamente esa "
                "área en el catálogo SEP consultado (datos de abril de 2021). "
                "Esto no significa que no existan otras opciones o carreras afines."
            ),
        }

    mensaje = "Hay programas cuyo nombre ofrece pistas directas sobre el tema."
    if temas_ausentes:
        mensaje += (
            " No encontré títulos con pistas directas de: "
            + ", ".join(temas_ausentes) + "."
        )
    return {
        "estado": "cobertura_directa", "temas": temas,
        "temas_prioritarios": temas_prioritarios,
        "temas_sin_cobertura": temas_ausentes, "ids_validos": ids,
        "mensaje": mensaje,
    }
