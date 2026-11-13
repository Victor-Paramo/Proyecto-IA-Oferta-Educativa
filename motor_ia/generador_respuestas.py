"""Presentación textual fundamentada en las ofertas recuperadas de PostgreSQL.

Los programas de exploración semántica se agrupan por institución para conservar
las modalidades registradas sin asociarlas a una institución diferente.
"""

from collections import defaultdict

from motor_ia.afinidades_academicas import NOMBRES_AREAS


FUENTE = 'Fuente: registros SEP de abril de 2021; verifica su vigencia actual.'


def nombre_limpio(nombre):
    return nombre[3:] if nombre.startswith('EN ') else nombre


def respuesta_sin_cobertura(temas, hay_afinidades):
    areas = ', '.join(NOMBRES_AREAS.get(tema, tema) for tema in temas)
    mensaje = (
        f'Identifiqué tu interés en {areas}. No encontré programas cuyos '
        'nombres indiquen directamente esa especialidad en el catálogo consultado. '
        'Esto no significa que no existan en otras instituciones.'
    )
    if hay_afinidades:
        mensaje += (
            '\nPuedo buscar carreras de áreas generales afines registradas '
            'en nuestra base, sin presentarlas como especialidades equivalentes.'
            '\n¿Quieres que te muestre esas opciones afines? (sí/no)'
        )
    else:
        mensaje += '\nTampoco identifiqué opciones afines mediante las reglas actuales.'
    return mensaje + '\n' + FUENTE


def _resumen_instituciones(programa, ofertas):
    """Genera fichas de cuatro campos compatibles con la interfaz de escritorio.

    Cada ficha corresponde a una institución. Las modalidades se obtienen de
    todas las ofertas de ese programa en dicha institución, no de ofertas[0].
    """
    grupos = defaultdict(list)
    for oferta in ofertas:
        grupos[oferta['institucion']].append(oferta)

    lineas = []
    for institucion, registros in sorted(grupos.items()):
        modalidades = sorted({str(o['modalidad']) for o in registros if o.get('modalidad')})
        planteles = sorted({str(o['plantel']).strip() for o in registros if o.get('plantel')})
        texto_planteles = (
            'Planteles: ' + ', '.join(planteles)
            if planteles else 'Plantel no especificado'
        )
        total = len(registros)
        texto_modalidades = 'Modalidades: ' + ', '.join(modalidades)
        if total > 1:
            texto_modalidades += f' ({total} ofertas registradas)'
        linea = (
            f'- {institucion} | {nombre_limpio(programa)} | '
            f'{texto_planteles} | {texto_modalidades}'
        )
        lineas.append(linea)
    return lineas


def respuesta_afinidades(resultados, temas, limite=10):
    if not resultados:
        return 'No encontré ofertas verificables de carreras afines en este catálogo.\n' + FUENTE

    encabezado = (
        'Encontré estas opciones de formación general potencialmente afines. '
        'NO son carreras especializadas en ' + ', '.join(
            NOMBRES_AREAS.get(t, t) for t in temas
        ) + '.\n'
        'La relación es orientativa: no se han verificado planes de estudio ni salidas laborales.'
    )
    lineas = [encabezado]
    for resultado in resultados[:limite]:
        area = NOMBRES_AREAS.get(
            resultado['area_afin'], resultado['area_afin']
        )
        fichas = _resumen_instituciones(
            resultado['nombre'], resultado['ofertas']
        )
        lineas.extend(
            f'{ficha} - Area afin: {area}' for ficha in fichas
        )
    lineas.append('¿Quieres consultar cuáles de esas opciones son mixtas, escolarizadas o no escolarizadas?')
    lineas.append(FUENTE)
    return '\n'.join(lineas)


def respuesta_programas(resultados, temas):
    if not resultados:
        return 'No encontré ofertas verificables para esos programas.\n' + FUENTE
    cantidad = len(resultados)
    sustantivo = 'programa' if cantidad == 1 else 'programas'
    lineas = [
        f'Encontré {cantidad} {sustantivo} relacionados con: {", ".join(temas)}.',
        'La relación es temática y no constituye una recomendación vocacional definitiva.',
        'Las modalidades se resumen por institución a partir de todas las ofertas registradas.',
    ]

    for resultado in resultados:
        ofertas = resultado['ofertas']
        if ofertas:
            lineas.extend(_resumen_instituciones(resultado['programa'], ofertas))

    lineas.extend([
        '¿Quieres ver las opciones mixtas, escolarizadas o no escolarizadas?',
        FUENTE,
    ])
    return '\n'.join(lineas)


def respuesta_ofertas(resultados, contexto, limite=15):
    if not resultados:
        return 'No encontré ofertas que cumplan esos filtros en el catálogo consultado.\n' + FUENTE
    institucion = contexto.get('institucion')
    programa = contexto.get('programa')
    modalidad = contexto.get('modalidad')
    filtros = []
    if programa:
        filtros.append(nombre_limpio(programa['nombre']))
    if institucion:
        filtros.append(institucion['nombre'])
    if modalidad:
        filtros.append('modalidad ' + modalidad.lower())
    cantidad = len(resultados)
    sustantivo = 'oferta' if cantidad == 1 else 'ofertas'
    lineas = [f'Encontré {cantidad} {sustantivo}' + (f' para {", ".join(filtros)}.' if filtros else '.')]
    for oferta in resultados[:limite]:
        lineas.append(
            f"- {oferta['institucion']} | {nombre_limpio(oferta['programa'])} | "
            f"{oferta['plantel'] or 'Plantel no especificado'} | {oferta['modalidad']}"
        )
    if len(resultados) > limite:
        lineas.append(f'Muestro {limite} de {len(resultados)} ofertas.')
    lineas.extend([
        'Puedes pedirme otro programa, institución o modalidad.',
        FUENTE,
    ])
    return '\n'.join(lineas)
