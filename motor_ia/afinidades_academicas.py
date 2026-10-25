"""Alternativas academicas afines, basadas SOLO en titulos del catalogo.

Las relaciones entre areas son orientativas, NO equivalencias de carreras,
planes de estudio ni evidencia de especializacion profesional.
Nunca se inventan programas: todos provienen de la lista consultada en PostgreSQL.
"""
import re
import unicodedata


def normalizar_titulo(texto):
    texto = unicodedata.normalize('NFD', texto.lower())
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9\s]', ' ', texto)).strip()


# Estas relaciones generales sirven para ofrecer ALTERNATIVAS, no para
# afirmar que un programa forma especialistas en meteorologia, astronomia, etc.
AREAS_AFINES = {
    'meteorologia': ('fisica', 'matematicas'),
    'astronomia': ('fisica', 'matematicas'),
    'aeroespacial': ('mecanica', 'fisica', 'matematicas'),
    'paleontologia': ('geologia', 'biologia'),
    'arqueologia': ('antropologia', 'historia'),
    'geologia': ('fisica', 'matematicas', 'biologia'),
    'ciencia_datos': ('matematicas', 'software'),
    'aeronautica': ('mecanica', 'fisica', 'telecomunicaciones'),
    'biomedica': ('mecatronica', 'biotecnologia'),
    'genetica': ('biotecnologia', 'biologia'),
    'biotecnologia': ('biotecnologia', 'biologia'),
    'astrobiologia': ('biologia', 'fisica'),
    'realidad_aumentada': ('interactiva', 'software'),
    'telecomunicaciones': ('telecomunicaciones', 'electronica'),
}

# Coincidencias CONSERVADORAS sobre el nombre completo del programa.
# Ej.: 'EN EDUCACION FISICA' NO se equipara con 'EN FISICA'.
PATRONES_TITULO = {
    'fisica': (
        r'^(?:en )?fisica(?: aplicada)?$',
        r'^(?:en )?ingenieria (?:en )?fisica$',
        r'^(?:en )?ciencias fisicas$',
    ),
    'matematicas': (
        r'^(?:en )?matematicas?(?: aplicadas?)?$',
        r'^(?:en )?ingenieria (?:en )?matematica$',
    ),
    'mecanica': (
        r'^(?:en )?ingenieria (?:en )?mecanica$',
        r'^(?:en )?ingenieria mecanica electrica$',
        r'^(?:en )?ingenieria (?:en )?mecatronica$',
        r'^(?:en )?ingeniero en mecatronica$',
    ),
    'geologia': (
        r'^(?:en )?geologia$',
        r'^(?:en )?ciencias de la tierra$',
    ),
    'biologia': (
        r'^(?:en )?biologia(?: experimental)?$',
        r'^(?:en )?ciencias biologicas$',
    ),
    'antropologia': (
        r'^(?:en )?antropologia(?: social)?$',
    ),
    'historia': (
        r'^(?:en )?historia$',
    ),
    'mecatronica': (
        r'^(?:en )?ingenieria (?:en )?mecatronica$',
        r'^(?:en )?ingeniero en mecatronica$',
    ),
    'biotecnologia': (
        r'^(?:en )?biotecnologia$',
        r'^(?:en )?ingenieria (?:en )?biotecnologia$',
    ),
    'interactiva': (
        r'^(?:en )?ingenieria en tecnologia interactiva en animacion digital$',
        r'^(?:en )?desarrollo de software interactivo y videojuegos$',
    ),
    'telecomunicaciones': (
        r'^(?:en )?ingenieria (?:en )?telecomunicaciones$',
        r'^(?:en )?ingenieria (?:en )?telematica$',
        r'^(?:en )?ingenieria electronica y comunicaciones$',
    ),
    'electronica': (
        r'^(?:en )?ingenieria (?:en )?electronica$',
    ),
    'software': (
        r'^(?:en )?ingenieria (?:en |de )?software$',
        r'^(?:en )?ingenieria (?:en )?desarrollo de software$',
        r'^(?:en )?informatica$',
    ),
}

PATRONES = {
    area: [re.compile(p) for p in patrones]
    for area, patrones in PATRONES_TITULO.items()
}

NOMBRES_AREAS = {
    'meteorologia': 'Meteorología',
    'astronomia': 'Astronomía',
    'aeroespacial': 'Ingeniería aeroespacial',
    'paleontologia': 'Paleontología',
    'arqueologia': 'Arqueología',
    'fisica': 'Física',
    'matematicas': 'Matemáticas',
    'mecanica': 'Ingeniería mecánica o mecatrónica',
    'biologia': 'Biología',
    'antropologia': 'Antropología',
    'historia': 'Historia',
    'geologia': 'Geología y ciencias de la Tierra',
    'ciencia_datos': 'Ciencia de datos',
    'software': 'Software e informática',
    'aeronautica': 'Aeronáutica',
    'biomedica': 'Ingeniería biomédica',
    'genetica': 'Genética',
    'realidad_aumentada': 'Realidad aumentada',
    'telecomunicaciones': 'Telecomunicaciones',
    'mecatronica': 'Mecatrónica',
    'biotecnologia': 'Biotecnología',
    'astrobiologia': 'Astrobiología',
    'interactiva': 'Tecnologías interactivas',
    'electronica': 'Electrónica',
}


def buscar_afinidades(temas, programas, limite=5):
    """Devuelve [{id_programa,nombre,area_afin}] desde filas reales (id,nombre).

    Primero intercala disciplinas para evitar que una sola ocupe las 5 plazas.
    No modifica la BD ni deduce los contenidos de los planes de estudio.
    """
    if limite < 1:
        return []
    areas = list(dict.fromkeys(
        area for tema in temas for area in AREAS_AFINES.get(tema, ())
    ))
    grupos = {area: [] for area in areas}
    for id_programa, nombre in programas:
        titulo = normalizar_titulo(nombre)
        for area in areas:
            if any(p.fullmatch(titulo) for p in PATRONES[area]):
                grupos[area].append({
                    'id_programa': int(id_programa),
                    'nombre': nombre,
                    'area_afin': area,
                })
                break

    # Reparto equilibrado por area, sin duplicados.
    resultado, vistos = [], set()
    indice = 0
    while len(resultado) < limite and any(indice < len(grupos[a]) for a in areas):
        for area in areas:
            if indice < len(grupos[area]):
                candidato = grupos[area][indice]
                if candidato['id_programa'] not in vistos:
                    resultado.append(candidato)
                    vistos.add(candidato['id_programa'])
                    if len(resultado) == limite:
                        break
        indice += 1
    return resultado
