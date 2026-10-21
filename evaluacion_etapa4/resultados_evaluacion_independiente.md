# Etapa 4 — Evaluación independiente y seguimiento de correcciones

## 1. Propósito y alcance

El proyecto **Oferta Educativa Ciudad de México 2.0** integra un clasificador de intenciones (TF-IDF y regresión logística), búsqueda semántica mediante MiniLM, recuperación de ofertas en PostgreSQL y contexto conversacional. La información académica procede de documentos SEP con fecha **30 de abril de 2021**; no garantiza disponibilidad vigente.

Esta etapa se diseñó para evaluar la capacidad del asistente de responder a preguntas diferentes de las utilizadas en el desarrollo. Se conservaron los resultados originales antes de corregir errores.

## 2. Evaluación independiente inicial: 20 preguntas

Se aplicaron **20 preguntas**, organizadas en cuatro sesiones de cinco turnos. Se registró si cada respuesta era correcta, parcial o incorrecta, atendiendo a interpretación, alcance de las ofertas, contexto, pertinencia y manejo de información no disponible.

| Resultado | Cantidad | Porcentaje |
|---|---:|---:|
| Correctas | 11 | 55 % |
| Parciales | 1 | 5 % |
| Incorrectas | 8 | 40 % |
| **Total** | **20** | **100 %** |

Estos valores reflejan la evaluación de las **20 preguntas originales**, no la exactitud del sistema ante todos los estudiantes.

### 2.1. Fallos detectados

| ID de prueba | Consulta problemática | Fallo observado |
|---|---|---|
| N03 | «¿Y si prefiero una modalidad mixta?» | Perdió Universidad del Valle de México y consultó ofertas mixtas de todo el catálogo (770). |
| N05 | «¿Qué opciones de esa institución son presenciales?» | Perdió Instituto SAE y consultó ofertas escolarizadas de todo el catálogo (1,657). |
| N13 | «Me gustaría comprender por qué se forman los tornados.» | No identificó Meteorología. |
| N14 | «Cambiando de tema, me gustaría estudiar terremotos y volcanes.» | No identificó Geología ni Ciencias de la Tierra. |
| N15 | «Quiero usar datos para descubrir patrones y hacer predicciones.» | No identificó Ciencia de Datos. |
| N16 | «¿Qué becas puedo solicitar para estudiar Contaduría?» | Mostró ofertas de Contaduría sin responder sobre becas. |
| N18 | «¿Las carreras que muestras siguen vigentes este año?» | Respondió con una pregunta sobre modalidades en lugar de explicar la limitación temporal. |
| N20 | «Gracias por la orientación; nos vemos pronto.» | No reconoció la despedida. |

La pregunta N11 («Me gusta dibujar personajes para videojuegos») fue evaluada como **parcial**: los programas recuperados eran relacionados, pero no se distinguían suficientemente los enfoques artísticos de los de programación.

## 3. Correcciones implementadas

### 3.1. Memoria conversacional

Se amplió la detección de referencias a instituciones y filtros previos, por ejemplo «¿Y si prefiero una modalidad mixta?» y «esa institución». Se actualizaron las reglas de `motor_ia/contexto.py`, manteniendo la capacidad de cambiar de universidad sin arrastrar filtros de una búsqueda anterior.

**Reevaluación observada:**

- Universidad del Valle de México: 367 ofertas iniciales, 24 no escolarizadas y **149 mixtas**, conservando la institución.
- Instituto SAE: 10 ofertas iniciales y **6 escolarizadas** en el seguimiento.

### 3.2. Comprensión de intereses académicos

Se ampliaron las señales lingüísticas de `motor_ia/validacion_cobertura_tematica.py` y las anotaciones temáticas auxiliares de `motor_ia/descripciones_tematicas.py`; se revisaron afinidades en `motor_ia/afinidades_academicas.py`.

**Reevaluación observada:**

- Tornados → **Meteorología**, sin afirmar que el catálogo contenga una carrera directa; ofrece explorar áreas afines.
- Terremotos y volcanes → **Geología y Ciencias de la Tierra**, con la misma precaución.
- Datos, patrones y predicciones → **Ciencia de Datos** e **Ingeniería en Ciencia de Datos**, recuperados del catálogo.

Se detectó y corrigió adicionalmente una regresión: «programar mundos virtuales» se confundía con una modalidad no escolarizada. Tras ajustar `motor_ia/interpretar_modalidades.py`, volvieron a recuperarse cinco programas relacionados con videojuegos sin ese filtro indebido.

### 3.3. Consultas generales y cortesía

Se ampliaron las reglas de `motor_ia/interaccion_general.py` para reconocer becas, vigencia de los registros y despedidas combinadas con agradecimientos.

**Reevaluación observada:**

- Becas → informa que no dispone de convocatorias ni ayudas económicas verificadas.
- Vigencia → aclara expresamente que la fuente es de **abril de 2021** y no confirma disponibilidad actual.
- «Gracias por la orientación; nos vemos pronto» → despedida adecuada y cierre del programa.

## 4. Pruebas de regresión

La última ejecución de la batería automatizada comunicada fue:

```text
185 passed in 0.81s
```

Las pruebas automatizadas comprueban casos específicos de las reglas implementadas. También se ejecutaron conversaciones reales mediante `app.py` y PostgreSQL para reevaluar los ocho errores.

## 5. Reevaluación de los ocho errores

| Grupo | Casos inicialmente incorrectos | Reevaluación |
|---|---:|---|
| Contexto (N03, N05) | 2 | 2 respuestas satisfactorias |
| Intereses (N13, N14, N15) | 3 | 3 respuestas satisfactorias |
| Consultas generales (N16, N18, N20) | 3 | 3 respuestas satisfactorias |
| **Total** | **8** | **8/8 casos repetidos satisfactorios** |

**Interpretación metodológica:** este resultado demuestra que se corrigieron los errores conocidos **en los casos repetidos**, no que la exactitud independiente haya pasado de 55 % a 100 %. Las 20 calificaciones originales **no se modifican**. Una evaluación con preguntas verdaderamente inéditas será necesaria para estimar generalización tras los cambios.

## 6. Limitaciones y actividades pendientes

- La detección de temas y las afinidades usan reglas auxiliares, no planes de estudio oficialmente verificados.
- MiniLM recupera similitud semántica, pero la similitud no equivale a pertinencia vocacional garantizada.
- La orientación solo es verificable respecto de las ofertas y modalidades incluidas en la base local, basada en registros históricos de 2021.
- La pregunta N11 permanece **parcial** en la evaluación original; todavía se puede mejorar la distinción entre coincidencias directas y carreras afines.
- Pendiente: **nueva evaluación con preguntas inéditas**, verificación de instalación reproducible y automatización de descarga de MiniLM, cierre documental y preparación de la demostración.


