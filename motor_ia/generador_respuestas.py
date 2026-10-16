"""Presentacion textual sin modelos generativos.

Solo usa nombres, modalidades y planteles proporcionados por PostgreSQL.
Fuente: catalogo SEP de abril de 2021 (no disponibilidad en tiempo real).
"""

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
        oferta = resultado['ofertas'][0]
        total = len(resultado['ofertas'])
        linea = (
            f"- {nombre_limpio(resultado['nombre'])} | "
            f"{oferta['institucion']} | {oferta['modalidad']} | "
            f"Área afín: {NOMBRES_AREAS[resultado['area_afin']]}"
        )
        if total > 1:
            linea += f' ({total} ofertas registradas)'
        lineas.append(linea)
    lineas.append('¿Quieres consultar cuáles de esas opciones son mixtas, escolarizadas o no escolarizadas?')
    lineas.append(FUENTE)
    return '\n'.join(lineas)


def respuesta_programas(resultados, temas):
    if not resultados:
        return 'No encontré ofertas verificables para esos programas.\n' + FUENTE
    lineas = [
        f'Encontré {len(resultados)} programas relacionados con: {", ".join(temas)}.',
        'Son coincidencias temáticas exploratorias, no una recomendación vocacional definitiva.',
    ]
    for resultado in resultados:
        ofertas = resultado['ofertas']
        if ofertas:
            oferta = ofertas[0]
            linea = (
                f"- {nombre_limpio(resultado['programa'])} | "
                f"{oferta['institucion']} | {oferta['modalidad']}"
            )
            if len(ofertas) > 1:
                linea += f' ({len(ofertas)} ofertas registradas)'
            lineas.append(linea)
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
