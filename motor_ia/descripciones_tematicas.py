"""Experimento: anotaciones tematicas INFERIDAS DEL NOMBRE, no oficiales SEP.

No contiene descripciones de planes de estudio, materias, requisitos, campus ni
salidas laborales. Una etiqueta solo se asigna si existe una pista expresa en
el titulo del programa. Las reglas son ejemplos editables y auditables.
"""
import re
import unicodedata


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texto).strip()


# (area, patron sobre nombre normalizado, descripcion tematica auxiliar)
# IMPORTANTE: Esta informacion NO proviene de los documentos SEP.
AREAS = (
    ("videojuegos", r"\bvideojuegos?\b", "videojuegos y juegos digitales"),
    ("animacion", r"\banimacion\b", "animacion digital y medios visuales"),
    ("software", r"\bsoftware\b|\bprogramacion\b|\binformatica\b|\bcomputacion\b", "software y tecnologias de computacion"),
    ("robotica", r"\brobotica\b|\bmecatronica\b", "robotica, mecatronica y sistemas automatizados"),
    ("electronica", r"\belectronica\b", "electronica y circuitos electronicos"),
    ("psicologia", r"\bpsicologia\b", "psicologia y estudio del comportamiento humano"),
    ("derecho", r"\bderecho\b|\bjuridic[a-z]*\b", "derecho, leyes y sistemas juridicos"),
    ("arquitectura", r"\barquitectura\b|\burbanismo\b", "arquitectura, diseno de espacios y urbanismo"),
    ("administracion", r"\badministracion\b|\bgestion empresarial\b|\bgestion de empresas\b", "administracion, gestion y organizacion empresarial"),
    ("gastronomia", r"\bgastronomia\b|\bculinari[a-z]*\b", "gastronomia, cocina y alimentos"),
    ("turismo", r"\bturismo\b|\bturistic[a-z]*\b|\bhotelera\b|\bhoteles\b", "turismo y servicios de hospitalidad"),
    ("medicina", r"\bmedicina\b|\benfermeria\b", "salud, medicina y cuidados de enfermeria"),
    ("fisica", r"\bfisica\b", "fisica y fenomenos del mundo natural"),
    ("matematicas", r"\bmatematic[a-z]*\b", "matematicas y razonamiento matematico"),
    ("astronomia", r"\bastronomia\b|\bastrofisica\b", "astronomia y astrofisica"),
    ("aeroespacial", r"\baeroespacial\b|\bastronautic[a-z]*\b|\bingenieria espacial\b", "ingenieria y tecnologia aeroespacial"),
    ("aeronautica", r"\baeronautic[a-z]*\b", "ingenieria aeronautica y aeronaves"),
    ("meteorologia", r"\bmeteorologia\b|\batmosferic[a-z]*\b|\bclimatologia\b", "meteorologia, atmosfera y clima"),
    ("arqueologia", r"\barqueologia\b", "arqueologia y estudio de vestigios arqueologicos"),
    ("paleontologia", r"\bpaleontologia\b", "paleontologia y estudio de fosiles"),
    ("geologia", r"\bgeologia\b|\bgeociencias\b|\bciencias de la tierra\b", "geologia y ciencias de la Tierra"),
    ("ciencia_datos", r"\bciencia(?:s)? de datos\b|\banalisis de datos\b|\banalitica de datos\b|\bmineria de datos\b", "ciencia de datos y analisis de informacion"),
    ("biomedica", r"\bbiomedic[a-z]*\b|\bingenieria medica\b", "ingenieria biomedica"),
    ("biotecnologia", r"\bbiotecnologia\b|\bbiotecnologic[a-z]*\b", "biotecnologia"),
    ("astrobiologia", r"\bastrobiologia\b", "astrobiologia y estudio de la vida extraterrestre"),
    ("genetica", r"\bgenetic[a-z]*\b|\bgenomica\b", "genetica y genomica"),
    ("realidad_aumentada", r"\brealidad aumentada\b", "realidad aumentada"),
    ("telecomunicaciones", r"\btelecomunicaciones?\b|\btelematica\b", "telecomunicaciones y telematica"),
)


def describir_por_nombre(nombre):
    """Devuelve (texto_para_embedding, lista_de_areas), sin alterar nombre."""
    limpio = normalizar(nombre)
    detectadas = [(area, descripcion) for area, patron, descripcion in AREAS
                  if re.search(patron, limpio)]
    if not detectadas:
        return nombre, []  # Nunca inventar un area si el titulo no da evidencia.

    # La cadena enriquecida es un INSUMO EXPERIMENTAL, no fuente oficial.
    temas = "; ".join(descripcion for _, descripcion in detectadas)
    enriquecido = f"{nombre}. Temas sugeridos por el nombre: {temas}."
    return enriquecido, [area for area, _ in detectadas]
