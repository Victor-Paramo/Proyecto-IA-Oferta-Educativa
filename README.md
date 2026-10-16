# Proyecto de Inteligencia Artificial – Oferta Educativa Ciudad de México 2.0

Proyecto desarrollado para la asignatura de Inteligencia Artificial.

## Objetivo

Desarrollar un sistema para procesar, estructurar y analizar información de la oferta educativa, con énfasis inicial en las licenciaturas disponibles en la Ciudad de México.

El proyecto utiliza como fuente documentos PDF con registros oficiales de instituciones y programas educativos.

La arquitectura está preparada para ampliar posteriormente la cobertura al resto de México.

## Estado actual del proyecto (octubre de 2026)

El proyecto dispone de un **prototipo conversacional funcional** para consultar licenciaturas de Ciudad de México registradas en documentos SEP de **abril de 2021**. Combina PostgreSQL, clasificación de intenciones, búsqueda semántica con MiniLM, comprobación de cobertura temática, alternativas académicas afines y memoria de sesión. Los resultados describen registros históricos, **no disponibilidad comprobada para 2026**.

- **Preparación y base de datos:** extracción, normalización, carga y verificaciones de integridad realizadas.
- **Etapa 3 — motor conversacional:** funcionalidades principales integradas y probadas en escenarios concretos; quedan limitaciones de interpretación y alcance temático.
- **Etapa 4 — evaluación final y entrega:** pendiente una batería independiente de consultas, análisis de errores, documentación final y demostración.

Las cifras de evaluación del clasificador **no representan la exactitud del asistente completo**. Las reglas temáticas y de afinidad son auxiliares; no describen oficialmente los planes de estudio.

## Proceso realizado

Hasta el momento se han completado las siguientes etapas:

1. Extracción automática de tablas desde archivos PDF.
2. Conversión de la información extraída a formato JSON.
3. Integración de los registros de diferentes documentos.
4. Detección y revisión de inconsistencias de extracción.
5. Limpieza inicial y generación de un JSON consolidado.
6. Auditoría estructural y análisis de dependencias funcionales.
7. Elaboración del Modelo Entidad–Relación (MER).
8. Elaboración del modelo relacional y diseño de la normalización hasta 3FN.
9. Implementación de la base de datos en PostgreSQL.
10. Carga de los registros originales y de los catálogos académicos.
11. Integración de las licenciaturas de CDMX en la capa normalizada.
12. Primera etapa de consolidación y corrección de instituciones y planteles.
13. Verificación de integridad referencial y pruebas iniciales de consulta.
14. Consolidación adicional de nombres institucionales, planteles y programas; conservación de la trazabilidad documental.
15. Preparación de preguntas de entrenamiento y evaluación para el clasificador de intenciones.
16. Comparación de regresión logística, Naive Bayes y SVM lineal.
17. Implementación del reconocimiento de instituciones, programas y modalidades.
18. Desarrollo de consultas parametrizadas a PostgreSQL para recuperar ofertas.
19. Incorporación de MiniLM para buscar carreras por similitud semántica.
20. Implementación de contexto conversacional y filtros de seguimiento.
21. Evaluación exploratoria de recomendaciones semánticas mediante etiquetas de pertinencia 0, 1 y 2.
22. Desarrollo de reglas de cobertura temática para evitar coincidencias engañosas en áreas no respaldadas directamente por el catálogo.
23. Ampliación del entrenamiento de intenciones de 80 a 136 preguntas y prueba de TF-IDF de palabras y caracteres.
24. Incorporación de alternativas académicas afines verificadas en PostgreSQL, previa confirmación del estudiante.
25. Generación de respuestas conversacionales y pruebas unitarias y de integración de los principales flujos.

Los pasos 1–13 documentan la preparación de datos y la base de datos; los pasos 14–25 describen su evolución hacia el asistente conversacional. Este registro conserva **el orden de desarrollo**, no implica que todas las funciones estén libres de errores.

## Datos procesados

Se procesaron cuatro documentos PDF, obteniendo:

| Conjunto de datos | Registros |
|---|---:|
| Registros nacionales | 27,054 |
| Registros correspondientes a CDMX | 5,312 |
| Registros de licenciaturas de CDMX | 2,810 |

Los niveles académicos identificados son:

- Licenciatura
- Maestría
- Especialidad
- Doctorado
- Técnico Superior Universitario
- Profesional Asociado

Los 27,054 registros nacionales se encuentran almacenados en PostgreSQL dentro de la capa de origen. La normalización activa se concentra en las licenciaturas de Ciudad de México.

## Arquitectura de la base de datos

Se implementó una base de datos PostgreSQL 16 denominada `oferta_educativa`, organizada en dos esquemas:

- **`origen`:** conserva los registros extraídos de los PDF, los documentos fuente y sus vínculos documentales.
- **`catalogo`:** almacena las instituciones, planteles, estados, programas académicos, niveles, modalidades, ofertas educativas y autorizaciones.

Ambos esquemas pertenecen a la misma base de datos y se relacionan mediante claves foráneas.

### Modelo Entidad–Relación (MER)

El modelo conceptual representa las entidades, sus atributos, las relaciones entre ellas y las cardinalidades.

![Modelo Entidad–Relación](diagramas/modelo_entidad_relacion.png)

### Modelo relacional

El modelo relacional muestra las tablas, sus atributos, claves primarias, claves foráneas y restricciones de unicidad.

![Modelo relacional](diagramas/modelo_relacional.png)

### Normalización

El diseño de la capa `catalogo` contempla la aplicación de los principios de Primera, Segunda y Tercera Forma Normal (1FN, 2FN y 3FN).

Se separaron las entidades académicas para reducir la redundancia y representar correctamente las relaciones entre instituciones, planteles, programas, modalidades y autorizaciones.

La capa `origen` mantiene los datos documentales para conservar la trazabilidad y facilitar futuras revisiones.

## Estado del catálogo en PostgreSQL

### Corte inicial de la normalización (registro histórico)

Después de la carga inicial y las primeras correcciones, se obtuvieron los siguientes resultados. **Esta tabla corresponde a ese corte y no debe confundirse con un conteo actualizado en tiempo real:**

| Tabla | Registros |
|---|---:|
| `catalogo.institucion` | 258 |
| `catalogo.plantel` | 326 |
| `catalogo.estado` | 32 |
| `catalogo.nivel_academico` | 6 |
| `catalogo.modalidad` | 3 |
| `catalogo.programa_academico` | 588 |
| `catalogo.oferta_educativa` | 2,616 |
| `catalogo.autorizacion` | 2,740 |
| `origen.registro_origen` | 27,054 |
| `origen.vinculo_registro` | 2,810 |

**Nota:** las 2,810 filas documentales de licenciatura de CDMX están vinculadas a 2,616 ofertas educativas en la capa normalizada. Ambos valores representan conceptos diferentes y no deben confundirse.

En este corte inicial, los 2,810 vínculos se conservaron en estado `REVISAR` mientras continuaba la validación de identidades institucionales y autorizaciones. Su estado más reciente debe verificarse en PostgreSQL.

### Consolidación posterior y alcance de las búsquedas

En las iteraciones posteriores se reportaron **226 instituciones consolidadas** y **588 nombres de programas** para la capa de consulta, junto con **2,616 ofertas normalizadas** y **2,810 vínculos a registros de origen**. Es importante no sumar registros de origen con ofertas normalizadas: representan conceptos diferentes.

Las cantidades exactas pueden variar si se realizan nuevas correcciones; para confirmar el estado actual se deben ejecutar consultas de conteo sobre la base de datos local.

## Limpieza y mejora de los datos

Se inició una segunda etapa de depuración sobre las entidades normalizadas en PostgreSQL.

Durante esta fase se consolidaron denominaciones de seis instituciones:

- Instituto Tecnológico y de Estudios Superiores de Monterrey.
- Universidad Tecnológica de México (UNITEC).
- Universidad de Londres.
- Universidad Insurgentes.
- Universidad La Salle.
- Universidad Panamericana.

Las correcciones se realizaron mediante transacciones SQL, actualizando relaciones entre instituciones y planteles y eliminando registros duplicados únicamente después de comprobar que no contenían referencias necesarias.

Las verificaciones confirmaron que permanecen las 2,616 ofertas educativas, las 2,740 autorizaciones y los 2,810 vínculos documentales.

Las correcciones realizadas se documentan en `limpieza_catalogo_cdmx_historial.md`.

Las verificaciones y correcciones adicionales se registraron progresivamente; los casos no resueltos deben consultarse en el historial y en los datos actuales de PostgreSQL.

## Consultas y validaciones

Se implementaron consultas SQL para comprobar:

- La cantidad de registros nacionales y de licenciaturas de CDMX.
- La integridad de las relaciones entre ofertas y registros originales.
- La existencia de instituciones y planteles duplicados.
- La conservación de ofertas, autorizaciones y vínculos después de las correcciones.
- La búsqueda de licenciaturas por nombre de programa, institución y modalidad.

Las consultas de verificación están disponibles en la carpeta `sql/`.

## Estructura del proyecto

- `PDFs/`: documentos PDF utilizados como fuente.
- `datos/`: archivos JSON, CSV y resultados de análisis locales.
- `diagramas/`: modelos conceptual y relacional.
- `scripts/`: programas Python de extracción, limpieza, auditoría y carga.
- `sql/`: instrucciones de creación y verificación de PostgreSQL.
- `motor_ia/`: clasificador, interpretación, búsqueda semántica, cobertura temática, afinidades y generación de respuestas.
- `funciones/`: consultas parametrizadas de programas, instituciones y modalidades.
- `tests/`: pruebas automatizadas de los componentes conversacionales.
- `app.py`: punto de entrada del asistente de consola.
- `modelos_ia/`: pesos descargados localmente de MiniLM (**excluidos de Git**).
- `limpieza_catalogo_cdmx_historial.md`: historial de correcciones del catálogo.
- `.gitignore`: configuración de archivos excluidos del control de versiones.
- `README.md`: documentación del proyecto.

## Tecnologías utilizadas

- Python 3.12
- pdfplumber
- JSON
- PostgreSQL 16
- psycopg2-binary
- scikit-learn (TF-IDF y regresión logística)
- Sentence Transformers y MiniLM multilingüe (embeddings)
- PyTorch (ejecución de MiniLM a través de sus dependencias)
- pytest (pruebas automatizadas)
- Git y GitHub

## Evolución del proyecto y siguientes etapas

**La extracción, la carga documental, el diseño de la base de datos y la integración inicial de licenciaturas de CDMX se realizaron.** En etapas posteriores también se implementó el asistente conversacional descrito más adelante.

### Plan inicial (conservado como historial)

Al concluir las primeras fases de normalización, se había definido el siguiente plan:

1. Continuar la limpieza controlada de instituciones y planteles.
2. Revisar autorizaciones y registros que presentan inconsistencias.
3. Consolidar y validar las consultas académicas.
4. Desarrollar la interfaz de búsqueda de licenciaturas de CDMX.
5. Incorporar las funcionalidades de Inteligencia Artificial.
6. Realizar pruebas funcionales y documentar los resultados.
7. Ampliar posteriormente la cobertura a nivel nacional.

**Alcance vigente del prototipo:** consultas sobre licenciaturas de Ciudad de México disponibles en el catálogo histórico consultado. La cobertura nacional sigue siendo una posibilidad de ampliación, no una función actual.

### Pendientes actuales

La recuperación SQL, MiniLM, la gestión de contexto y las respuestas conversacionales **ya se implementaron**. El trabajo siguiente se concentra en la evaluación integral independiente (etapa 4), corrección de errores detectados, documentación final, posible automatización de la descarga de MiniLM y presentación.

## Motor de inteligencia artificial — primera versión (histórico)

El proyecto incorpora un motor de procesamiento de lenguaje natural desarrollado en Python para interpretar consultas sobre la oferta educativa de licenciaturas en Ciudad de México.

### Componentes implementados

| Archivo | Descripción |
|---|---|
| `scripts/10_normalizar_consultas.py` | Normaliza preguntas en español, eliminando diferencias de mayúsculas, acentos y puntuación. |
| `motor_ia/clasificador.py` | Implementa un clasificador de intenciones mediante TF-IDF y regresión logística. |
| `motor_ia/comparar_modelos.py` | Compara regresión logística, Naive Bayes y SVM lineal mediante validación cruzada y evaluación independiente. |
| `motor_ia/entidades.py` | Identifica instituciones, programas académicos y modalidades consultando los catálogos de PostgreSQL. |
| `motor_ia/interpretar_consulta.py` | Integra la clasificación de intenciones con la extracción de entidades y produce una interpretación estructurada de cada pregunta. |

### Clasificación de intenciones

El **conjunto inicial** de entrenamiento contenía 80 preguntas etiquetadas, distribuidas entre cuatro categorías. Posteriormente se amplió a 136; los resultados de esa actualización se encuentran al final de este documento:

- `buscar_programa`
- `buscar_institucion`
- `filtrar_modalidad`
- `explorar_area`

Se preparó un conjunto independiente de 24 preguntas para evaluar el comportamiento de los algoritmos.

### Resultados experimentales

| Algoritmo | Validación cruzada | Evaluación independiente |
|---|---:|---:|
| Regresión logística | 96.25% | 91.67% |
| Naive Bayes | 92.50% | 87.50% |
| SVM lineal | 95.00% | 87.50% |

En esta comparación inicial se seleccionó provisionalmente la regresión logística, debido a su desempeño y facilidad de interpretación; posteriormente se mantuvo y amplió el entrenamiento.

### Ejecución

Desde la carpeta principal del proyecto, con el entorno virtual y las dependencias instaladas:

**Comparar algoritmos**
```powershell
.\.venv\Scripts\python.exe motor_ia\comparar_modelos.py
```
**Probar la extracción de entidades**
```powershell
.\.venv\Scripts\python.exe motor_ia\entidades.py
```
**Interpretar consultas completas**
```powershell
.\.venv\Scripts\python.exe motor_ia\interpretar_consulta.py
```
Los módulos que acceden a PostgreSQL solicitan la contraseña mediante `getpass()` y utilizan la base de datos local `oferta_educativa`.

### Estado de la primera versión (histórico)

La primera integración del motor de IA permitió clasificar la intención del usuario y reconocer instituciones, programas y modalidades a partir de consultas en español.

**En ese momento** aún estaban pendientes la recuperación de ofertas, la búsqueda semántica, el contexto conversacional y las respuestas fundamentadas. **Esos componentes se desarrollaron después**, como se documenta en los apartados de la etapa 3 y su actualización.

**Nota:** Los datos oficiales utilizados provienen de documentos de la SEP con información actualizada al 30 de abril de 2021. Los resultados deben interpretarse considerando esa limitación temporal.

---

## Etapa 3. Desarrollo inicial y experimentos (registro histórico)

> Este apartado conserva los experimentos, valores y problemas de la **primera integración**. Algunas limitaciones descritas aquí se resolvieron más adelante; para el estado más reciente, consulta la actualización final de la etapa 3. No confundir la puntuación inicial de MiniLM con las respuestas del prototipo actual.

### 1. Objetivo

Durante esta etapa se desarrolló e integró el motor de inteligencia artificial del proyecto **Oferta Educativa Ciudad de México 2.0**, con el objetivo de permitir que los estudiantes consulten programas académicos mediante preguntas formuladas en lenguaje natural.

El sistema combina diferentes técnicas de inteligencia artificial y recuperación de información:

- Clasificación de intenciones mediante aprendizaje automático.
- Reconocimiento de entidades presentes en las preguntas.
- Búsquedas estructuradas mediante PostgreSQL.
- Búsqueda semántica utilizando embeddings.
- Recuperación de instituciones, programas, planteles y modalidades.
- Memoria y contexto conversacional.

La información procede de documentos de oferta educativa de la Secretaría de Educación Pública (SEP), fechados el **30 de abril de 2021**.

Por tanto, los resultados corresponden a los registros disponibles en esas fuentes y no garantizan que las ofertas educativas continúen vigentes actualmente.

---

### 2. Desarrollo del clasificador de intenciones

Se desarrolló un modelo de clasificación supervisada mediante la biblioteca **scikit-learn**.

El propósito del clasificador es identificar qué desea consultar el estudiante y seleccionar el procedimiento adecuado para obtener una respuesta.

#### 2.1. Técnicas utilizadas

Se utilizaron:

- `TfidfVectorizer`: representación numérica de las preguntas.
- Unigramas y bigramas mediante `ngram_range=(1,2)`.
- `LogisticRegression`: clasificación supervisada de intenciones.
- Normalización de texto para facilitar el procesamiento.

En la versión inicial, el clasificador fue entrenado con **80 preguntas etiquetadas**; después se amplió a 136.

También se preparó un conjunto independiente de **24 preguntas de evaluación**.

#### 2.2. Intenciones reconocidas

| Intención | Descripción |
|---|---|
| `buscar_programa` | Buscar instituciones que ofrecen una carrera específica. |
| `buscar_institucion` | Consultar los programas de una institución educativa. |
| `filtrar_modalidad` | Buscar programas según su modalidad de estudio. |
| `explorar_area` | Identificar carreras relacionadas con los intereses del estudiante. |

#### 2.3. Comparación de algoritmos

Se evaluaron tres algoritmos de clasificación:

1. Regresión logística.
2. Naive Bayes multinomial.
3. Máquina de vectores de soporte lineal (Linear SVM).

Los resultados fueron:

| Algoritmo | Exactitud en validación cruzada | Exactitud independiente |
|---|---:|---:|
| Regresión logística | 96.25 % | 91.67 % |
| Naive Bayes multinomial | 92.50 % | 87.50 % |
| Linear SVM | 95.00 % | 87.50 % |

La regresión logística obtuvo **22 clasificaciones correctas de 24 preguntas independientes**, equivalentes a una exactitud de **91.67 %**.

Por este motivo, se seleccionó como clasificador principal del proyecto.

Es importante aclarar que esta exactitud corresponde únicamente a la clasificación de intenciones, no al funcionamiento completo del asistente conversacional.

Dado que el conjunto independiente contiene 24 preguntas, será necesario ampliar la evaluación para obtener conclusiones más sólidas.

---

### 3. Reconocimiento de entidades

Se implementó un módulo de reconocimiento de entidades que utiliza los catálogos almacenados en PostgreSQL.

Las entidades identificadas son:

- Instituciones educativas.
- Programas académicos.
- Modalidades de estudio.

El procedimiento incluye normalización de texto y comparación con los nombres existentes en la base de datos.

#### 3.1. Modalidades reconocidas

El sistema trabaja con tres modalidades:

| Modalidad | Expresiones relacionadas |
|---|---|
| ESCOLARIZADA | Presencial, escolarizada |
| MIXTA | Mixta, semipresencial |
| NO ESCOLARIZADA | A distancia, en línea, no escolarizada |

Estas equivalencias permiten reconocer diferentes expresiones utilizadas por los estudiantes.

El reconocimiento de entidades proporciona identificadores que posteriormente se utilizan en las consultas SQL.

---

### 4. Funciones de recuperación mediante PostgreSQL

Se incorporaron funciones específicas para recuperar información del catálogo académico.

Estas funciones se encuentran dentro del directorio `funciones/`.

#### 4.1. Archivos desarrollados

| Archivo | Responsabilidad |
|---|---|
| `funciones/buscar_programa.py` | Recuperar ofertas educativas de un programa académico. |
| `funciones/buscar_institucion.py` | Recuperar los programas ofrecidos por una institución. |
| `funciones/filtrar_modalidad.py` | Recuperar ofertas según la modalidad solicitada. |

Las funciones utilizan consultas SQL parametrizadas sobre las tablas normalizadas de PostgreSQL.

#### 4.2. Información recuperada

Las consultas permiten obtener:

- Nombre de la institución.
- Nombre del programa académico.
- Nombre del plantel, cuando está disponible.
- Modalidad educativa.
- Identificador de la oferta.

La información se recupera de registros reales almacenados en la base de datos.

No se generan nombres de instituciones ni programas inexistentes para completar las respuestas.

Cuando el nombre de un plantel no se encuentra registrado en la fuente, se utiliza el mensaje **Plantel no especificado**.

---

### 5. Incorporación de búsqueda semántica con MiniLM

Para permitir consultas basadas en intereses, se incorporó la biblioteca **Sentence Transformers**.

Se utilizó el modelo multilingüe previamente entrenado:

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Este modelo permite transformar textos en vectores numéricos llamados **embeddings**.

#### 5.1. ¿Qué son los embeddings?

Los embeddings son representaciones vectoriales que permiten comparar textos mediante operaciones matemáticas.

El modelo MiniLM utilizado genera vectores de **384 dimensiones**.

Por ejemplo, una pregunta como:

> Me gustaría desarrollar videojuegos y programar mundos virtuales.

Puede compararse con nombres de programas académicos como:

- Programación de Videojuegos.
- Ingeniería en Animación y Videojuegos.
- Desarrollo de Software Interactivo y Videojuegos.

El sistema no necesita que la pregunta contenga exactamente el nombre oficial de una carrera.

#### 5.2. Similitud del coseno

Para comparar los embeddings se utiliza la similitud del coseno:

$$
\mathrm{sim}(A,B) =
\frac{A \cdot B}{\lVert A \rVert \, \lVert B \rVert}
$$

Donde:

- $A$ es el vector correspondiente a la pregunta.
- $B$ es el vector correspondiente a un programa académico.
- $A\cdot B$ representa el producto punto.
- $\lVert A \rVert$ y $\lVert B \rVert$ representan las normas de los vectores.

Los programas se ordenan según sus puntuaciones de similitud.

Estas puntuaciones permiten establecer un orden de recuperación, pero no representan probabilidades de que una carrera sea adecuada para un estudiante.

#### 5.3. Programas utilizados

La búsqueda semántica trabaja con **588 nombres distintos de programas académicos** recuperados del catálogo de PostgreSQL.

Los embeddings de estos programas se calculan al iniciar la aplicación y se reutilizan durante la sesión.

De esta manera, no es necesario volver a calcular los embeddings del catálogo por cada pregunta.

#### 5.4. Archivos incorporados

| Archivo | Función |
|---|---|
| `motor_ia/12_probar_embeddings.py` | Descargar MiniLM y realizar pruebas iniciales de similitud. |
| `motor_ia/busqueda_semantica.py` | Comparar preguntas con programas académicos mediante embeddings. |
| `motor_ia/recuperacion_semantica.py` | Consultar las ofertas educativas asociadas a los programas encontrados. |

La utilización de MiniLM como modelo preentrenado fue consultada y autorizada por el profesor responsable del proyecto.

---

### 6. Instalación manual del modelo MiniLM

#### 6.1. ¿Por qué MiniLM no se incluye en GitHub?

**Los archivos del modelo MiniLM no se almacenan directamente en este repositorio.**

Esta decisión responde a las siguientes razones:

1. MiniLM es un modelo previamente entrenado y publicado por terceros.
2. Sus archivos de pesos neuronales ocupan cientos de megabytes.
3. GitHub establece límites de tamaño para los archivos almacenados mediante Git convencional.
4. El modelo puede descargarse nuevamente desde Hugging Face.
5. Durante esta etapa no se ha realizado un reentrenamiento ni ajuste de los pesos originales.
6. Se busca mantener el repositorio centrado en el código fuente, los datos de trabajo y la documentación.

La carpeta:

`modelos_ia/`

Se encuentra excluida mediante el archivo `.gitignore`.

Esto significa que el repositorio conserva los programas necesarios para utilizar MiniLM, pero no incluye los parámetros descargados del modelo neuronal.

#### 6.2. Requisitos previos

Para utilizar MiniLM es necesario contar con:

- Python instalado.
- Un entorno virtual configurado.
- Las dependencias del proyecto.
- Conexión a Internet durante la primera descarga.
- PostgreSQL configurado para las consultas del catálogo.

Los siguientes comandos están preparados para ejecutarse desde PowerShell, dentro de la carpeta principal del proyecto.

#### 6.3. Instalar Sentence Transformers

Si la biblioteca todavía no está instalada, ejecutar:
```powershell
.\.venv\Scripts\python.exe -m pip install sentence-transformers
```
Esta biblioteca permite cargar modelos preentrenados y generar embeddings.

#### 6.4. Crear las carpetas locales

Crear la carpeta donde se guardará el modelo:
```powershell
mkdir modelos_ia
```
Después crear la subcarpeta:
```powershell
mkdir modelos_ia\minilm
```
Si ambas carpetas ya existen, no es necesario repetir estos pasos.

#### 6.5. Descargar el modelo

Ejecutar:
```powershell
.\.venv\Scripts\python.exe motor_ia\12_probar_embeddings.py
```
Durante la primera ejecución, el programa descarga desde Hugging Face el modelo:

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Posteriormente, lo guarda en:

`modelos_ia/minilm/`

La descarga puede tardar varios minutos, dependiendo de la conexión a Internet.

Una vez descargado, el modelo puede utilizarse localmente sin repetir el procedimiento.

#### 6.6. Comprobar la instalación

La ejecución correcta debe mostrar mensajes semejantes a:
```text
Modelo guardado correctamente.
Cantidad de textos: 3
Dimensiones de cada vector: 384
```
El programa también presenta las similitudes calculadas entre tres textos utilizados como ejemplos.

#### 6.7. Ejecutar la búsqueda semántica

Para probar MiniLM con los programas reales de PostgreSQL:
```powershell
.\.venv\Scripts\python.exe motor_ia\busqueda_semantica.py
```
Este programa permite escribir preguntas sobre intereses y consultar los programas académicos con mayor similitud.

Para ejecutar la recuperación de instituciones:
```powershell
.\.venv\Scripts\python.exe motor_ia\recuperacion_semantica.py
```
En esta prueba se muestran programas académicos, instituciones, planteles y modalidades registrados.

#### 6.8. Ejecutar el asistente completo

Después de instalar MiniLM y configurar PostgreSQL:
```powershell
.\.venv\Scripts\python.exe app.py
```
El sistema solicita la contraseña de PostgreSQL y prepara los modelos necesarios para procesar las preguntas.

#### 6.9. Mejora futura: descarga automática

En una actualización posterior se implementará la descarga automática de MiniLM.

El comportamiento previsto será:

1. Verificar si el modelo existe dentro de `modelos_ia/minilm/`.
2. Si existe, cargarlo desde el almacenamiento local.
3. Si no existe, intentar descargarlo desde Hugging Face.
4. Guardar el modelo descargado.
5. Continuar con el inicio de la aplicación.

**Esta funcionalidad todavía no está implementada en `app.py`.**

Por el momento, la instalación debe realizarse mediante el procedimiento manual descrito anteriormente.

---

### 7. Integración del motor de IA en app.py

El archivo `app.py` funciona como punto de entrada del asistente conversacional.

Durante el inicio de la aplicación se realizan las siguientes operaciones:

1. Preparar el clasificador de intenciones.
2. Establecer una conexión con PostgreSQL.
3. Recuperar las instituciones y programas académicos.
4. Cargar el modelo MiniLM desde el almacenamiento local.
5. Generar los embeddings de los 588 programas.
6. Inicializar la memoria conversacional.
7. Esperar preguntas del estudiante.

#### 7.1. Procesamiento de preguntas

Cuando el estudiante escribe una pregunta, el sistema identifica la intención y las entidades correspondientes.

Si se trata de una búsqueda por institución, programa o modalidad, utiliza las funciones de recuperación SQL.

Si identifica la intención `explorar_area`, utiliza MiniLM para localizar programas relacionados con los intereses expresados.

Posteriormente, PostgreSQL permite recuperar las instituciones y modalidades correspondientes.

#### 7.2. Flujo general
```text
Pregunta del estudiante
         |
         v
Clasificador de intenciones
         |
         v
Reconocimiento de entidades
         |
         v
Seleccion del procedimiento
         |
         +---------------------------+
         |                           |
         v                           v
Busqueda SQL                  Busqueda con MiniLM
         |                           |
         |                           v
         |                    Programas relacionados
         |                           |
         |                           v
         |                    Recuperacion SQL
         |                           |
         +-------------+-------------+
                       |
                       v
              Ofertas educativas
                       |
                       v
              Respuesta al usuario
```
El sistema utiliza PostgreSQL como fuente de información para verificar los programas e instituciones recuperados.

---

### 8. Memoria y contexto conversacional

Se amplió el módulo `motor_ia/contexto.py` para conservar información relevante de las consultas anteriores.

#### 8.1. Contexto tradicional

El sistema puede conservar:

- Institución educativa.
- Programa académico.
- Modalidad de estudio.

Por ejemplo:

**Pregunta inicial:**

> ¿Qué carreras ofrece la Universidad ICEL?

**Pregunta de seguimiento:**

> ¿Y cuáles son mixtas?

El sistema conserva la institución Universidad ICEL y aplica el filtro de modalidad mixta.

#### 8.2. Contexto semántico

Se incorporó la capacidad de conservar los identificadores de los programas encontrados mediante MiniLM.

Por ejemplo:

**Pregunta inicial:**

> Me gustaría desarrollar videojuegos y programar mundos virtuales.

El sistema encuentra cinco programas relacionados y guarda sus identificadores.

**Pregunta de seguimiento:**

> ¿Y cuáles de esas opciones son mixtas?

El sistema consulta únicamente las ofertas mixtas correspondientes a los programas encontrados.

**Nueva pregunta de seguimiento:**

> ¿Y cuáles son escolarizadas?

El sistema conserva los mismos programas, pero cambia el filtro a modalidad escolarizada.

#### 8.3. Cambio de tema

Cuando el estudiante formula una pregunta independiente, se inicia un nuevo contexto.

Por ejemplo:

> ¿Qué carreras ofrece la Universidad ICEL?

Esta consulta deja de utilizar los identificadores semánticos anteriores y recupera la oferta educativa correspondiente a la institución mencionada.

La memoria implementada funciona durante la sesión actual de ejecución del programa.

---

### 9. Pruebas de integración

Se realizaron pruebas utilizando PowerShell, Python y PostgreSQL.

#### 9.1. Búsqueda semántica sobre videojuegos

**Pregunta:**

> Me gustaría desarrollar videojuegos y programar mundos virtuales.

**Intención identificada:** `explorar_area`

**Confianza del clasificador:** 47.60 %

Los cinco programas recuperados fueron:

| Programa | Similitud |
|---|---:|
| Programación de Videojuegos | 0.4441 |
| Ingeniería en Animación y Videojuegos | 0.4340 |
| Ingeniería en Tecnología Interactiva en Animación Digital | 0.4164 |
| Desarrollo de Software Interactivo y Videojuegos | 0.4123 |
| Diseño de Animación Digital | 0.4110 |

Posteriormente se identificaron las instituciones correspondientes:

- Instituto SAE.
- Universidad Panamericana.
- Universidad del Valle de México.
- Instituto Universitario Amerike.
- Universidad Salesiana.

Esta prueba permitió comprobar la recuperación de programas relacionados con una descripción de intereses sin utilizar nombres exactos de carreras.

#### 9.2. Búsqueda semántica sobre electrónica y robótica

**Pregunta:**

> Me interesa diseñar circuitos electrónicos y construir robots.

Los programas con mayor similitud fueron:

| Programa | Similitud |
|---|---:|
| Ingeniería Electrónica | 0.5095 |
| Ingeniería Electrónica y Comunicaciones | 0.4917 |
| Ingeniería Industrial Electrónica | 0.4886 |
| Ingeniería en Sistemas Digitales y Robótica | 0.4837 |
| Ingeniería Industrial Eléctrica | 0.4837 |

Los resultados mostraron programas relacionados principalmente con electrónica, electricidad y robótica.

Sin embargo, la pertinencia de cada programa deberá evaluarse posteriormente, ya que la similitud semántica no garantiza que todas las opciones recuperadas satisfagan los intereses del estudiante.

#### 9.3. Seguimiento semántico: modalidad mixta

**Pregunta:**

> ¿Y cuáles de esas opciones son mixtas?

**Intención identificada:** `filtrar_modalidad`

**Confianza:** 49.70 %

El sistema conservó los cinco programas previamente encontrados y recuperó **3 ofertas educativas**:

| Institución | Programa | Plantel |
|---|---|---|
| Instituto SAE | Programación de Videojuegos | No especificado |
| Universidad del Valle de México | Ingeniería en Tecnología Interactiva en Animación Digital | San Rafael |
| Universidad del Valle de México | Ingeniería en Tecnología Interactiva en Animación Digital | Tlalpan |

Todas las ofertas recuperadas correspondieron a modalidad MIXTA.

#### 9.4. Seguimiento semántico: modalidad escolarizada

**Pregunta:**

> ¿Y cuáles son escolarizadas?

**Intención identificada:** `filtrar_modalidad`

**Confianza:** 49.38 %

El sistema conservó los cinco programas anteriores y recuperó **5 ofertas educativas**:

- Universidad Panamericana: Ingeniería en Animación y Videojuegos.
- Universidad del Valle de México, Coyoacán: Ingeniería en Tecnología Interactiva en Animación Digital.
- Universidad del Valle de México, San Rafael: Ingeniería en Tecnología Interactiva en Animación Digital.
- Instituto Universitario Amerike, Del Valle: Desarrollo de Software Interactivo y Videojuegos.
- Universidad Salesiana: Diseño de Animación Digital.

Todas las ofertas correspondieron a modalidad ESCOLARIZADA.

#### 9.5. Cambio de tema: Universidad ICEL

**Pregunta:**

> ¿Qué carreras ofrece la Universidad ICEL?

**Intención identificada:** `buscar_institucion`

**Confianza:** 68.14 %

**Resultado:** 313 ofertas educativas.

El sistema abandonó el contexto semántico de videojuegos y realizó una nueva consulta por institución.

Esto permitió comprobar que el cambio de tema funciona en el caso probado.

#### 9.6. Seguimiento tradicional: Universidad ICEL

**Pregunta:**

> ¿Y cuáles son mixtas?

**Intención identificada:** `filtrar_modalidad`

**Confianza:** 43.58 %

**Resultado:** 75 ofertas educativas.

El sistema conservó Universidad ICEL como institución y aplicó correctamente la modalidad MIXTA.

#### 9.7. Resumen de resultados

| Prueba | Resultado | Estado |
|---|---|---|
| Exploración semántica de videojuegos | 5 programas relacionados | Satisfactoria |
| Exploración semántica de electrónica | Programas relacionados recuperados | Satisfactoria |
| Seguimiento con modalidad mixta | 3 ofertas | Satisfactoria |
| Seguimiento con modalidad escolarizada | 5 ofertas | Satisfactoria |
| Cambio de tema a Universidad ICEL | 313 ofertas | Satisfactoria |
| Seguimiento tradicional sobre ICEL | 75 ofertas mixtas | Satisfactoria |

Los resultados corresponden a pruebas funcionales concretas y no representan una evaluación exhaustiva del asistente.

---

### 10. Limitaciones identificadas

Durante el desarrollo se identificaron aspectos que todavía requieren mejoras.

#### 10.1. Confianza del clasificador

Algunas preguntas fueron clasificadas con niveles de confianza relativamente bajos.

Por ejemplo:

- Exploración de videojuegos: 47.60 %.
- Seguimiento de modalidad mixta: 49.70 %.
- Seguimiento de modalidad escolarizada: 49.38 %.

Aunque estas consultas fueron interpretadas correctamente, es necesario estudiar el comportamiento del clasificador cuando recibe preguntas ambiguas o diferentes a las utilizadas durante el entrenamiento.

Las puntuaciones del clasificador tampoco deben interpretarse automáticamente como probabilidades perfectamente calibradas.

#### 10.2. Pertinencia semántica

MiniLM identifica programas mediante similitud vectorial, pero el programa con mayor puntuación no siempre será la opción más adecuada.

Se necesita evaluar:

- La pertinencia de las primeras recomendaciones.
- Las consultas que producen similitudes bajas.
- Los resultados poco relacionados con los intereses.
- Los casos en los que conviene solicitar información adicional.

En este experimento inicial, el sistema devolvía los cinco nombres de mayor similitud sin comprobar cobertura temática. Más adelante se incorporó una comprobación conservadora de cobertura y un flujo de carreras afines; esto **no sustituye** una evaluación integral independiente.

#### 10.3. Preguntas ambiguas

Se requiere mejorar la identificación de preguntas que no contienen información suficiente para ejecutar una búsqueda confiable.

En esos casos, el asistente deberá solicitar aclaraciones antes de mostrar resultados.

#### 10.4. Respuestas sin evidencia

Es necesario fortalecer los mecanismos para reconocer situaciones en las que no existan programas pertinentes en el catálogo.

El sistema no debe presentar una recomendación como confiable únicamente porque obtuvo una puntuación de similitud mayor que las demás.

#### 10.5. Respuestas conversacionales

En esta versión, la aplicación presentaba principalmente listados técnicos en terminal. Posteriormente se desarrolló un generador de respuestas conversacionales, aún dentro de la consola.

#### 10.6. Alcance temporal del catálogo

Los datos utilizados proceden de documentos SEP fechados el 30 de abril de 2021.

La aplicación debe informar esta limitación para evitar que los estudiantes interpreten las ofertas como información necesariamente vigente en 2026.

---

### 11. Mejoras pendientes para concluir la etapa 3

Al terminar este corte inicial, se habían identificado las siguientes actividades pendientes (se conservan como historial):

1. Incorporar mecanismos de manejo de preguntas ambiguas.
2. Evaluar criterios para rechazar resultados semánticos poco pertinentes.
3. Controlar consultas sin evidencia suficiente en PostgreSQL.
4. Mejorar la presentación conversacional de las respuestas.
5. Ampliar las pruebas de integración.
6. Implementar posteriormente la descarga automática de MiniLM.

Estos cambios deberán desarrollarse sin afectar las búsquedas y el contexto conversacional que ya funcionan.

---

### 12. Estado actual del proyecto

Al finalizar este avance, se cuenta con un prototipo funcional que integra:

**Clasificación de intenciones + reconocimiento de entidades + búsqueda semántica + PostgreSQL + memoria conversacional.**

El sistema puede:

- Interpretar preguntas sobre carreras, instituciones y modalidades.
- Recuperar ofertas educativas desde PostgreSQL.
- Identificar programas relacionados con intereses expresados en lenguaje natural.
- Recuperar las instituciones que ofrecen esos programas.
- Conservar resultados anteriores para aplicar filtros de modalidad.
- Reconocer cambios de tema en los casos probados.

En este corte aún faltaban controles de ambigüedad y cobertura; varias mejoras se implementaron después y se describen en la actualización de octubre de 2026.

Posteriormente se realizará la evaluación integral de la aplicación, incluyendo al menos 20 consultas, documentación de resultados y preparación de la demostración final.

---

### 13. Herramientas y tecnologías utilizadas

| Herramienta | Aplicación en el proyecto |
|---|---|
| Python | Desarrollo del asistente y procesamiento de datos. |
| PostgreSQL | Almacenamiento y recuperación de ofertas educativas. |
| psycopg2 | Conexión entre Python y PostgreSQL. |
| scikit-learn | Clasificación supervisada de intenciones. |
| TF-IDF | Representación vectorial de las preguntas del clasificador. |
| Sentence Transformers | Generación de embeddings semánticos. |
| MiniLM multilingüe | Comparación semántica entre preguntas y programas. |
| PyTorch | Ejecución del modelo neuronal mediante sus dependencias. |
| Visual Studio Code | Desarrollo y edición de archivos. |
| Git | Control de versiones. |
| GitHub | Respaldo y seguimiento del código fuente. |

---

### 14. Referencias técnicas

- **Secretaría de Educación Pública (SEP). (2021).** Documentos de oferta educativa utilizados como fuentes originales del catálogo, con fecha del 30 de abril de 2021.
- **Pedregosa, F., et al. (2011).** Scikit-learn: Machine Learning in Python. **Journal of Machine Learning Research, 12**, 2825-2830. https://scikit-learn.org/
- **Reimers, N., y Gurevych, I. (2019).** Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. **Proceedings of EMNLP-IJCNLP**. https://arxiv.org/abs/1908.10084
- **Sentence Transformers. (s. f.).** Sentence Transformers Documentation. https://www.sbert.net/
- **Hugging Face. (s. f.).** sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2. https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- **PostgreSQL Global Development Group. (s. f.).** PostgreSQL Documentation. https://www.postgresql.org/docs/
- **OpenAI. (2026).** ChatGPT [Modelo de lenguaje]. Consulta de apoyo para explicaciones técnicas, revisión de integración y preparación de documentación. https://chatgpt.com/

## Etapa 3. Actualización más reciente: asistente conversacional y carreras afines (octubre de 2026)

> Esta sección describe el **estado funcional más reciente probado** y complementa el historial anterior. El cierre formal y la medición de desempeño del asistente completo corresponden a la etapa 4.

### Objetivo de esta actualización

Integrar las búsquedas estructuradas en PostgreSQL, el clasificador de intenciones, MiniLM y la memoria conversacional para ofrecer respuestas comprensibles sobre licenciaturas registradas en Ciudad de México. El sistema distingue entre **programas directamente identificables por su nombre** y **alternativas académicas afines**.

> **Alcance de los datos:** el catálogo procede de documentos SEP fechados el **30 de abril de 2021**. Las ofertas mostradas son registros históricos, **no disponibilidad verificada para 2026**. Las relaciones entre carreras afines son orientativas y no certifican contenidos de planes de estudio ni salidas profesionales.

### Mejora del clasificador de intenciones

Se conservaron **TF-IDF y regresión logística**, ampliando el conjunto de entrenamiento de **80 a 136 preguntas etiquetadas** y probando una representación que combina palabras y fragmentos de palabras. Se mantienen cuatro intenciones: `buscar_programa`, `buscar_institucion`, `filtrar_modalidad` y `explorar_area`.

| Evaluación | Versión original | Versión mejorada |
|---|---:|---:|
| 40 preguntas de diagnóstico | 33/40 (82.50 %) | 37/40 (92.50 %) |
| 24 preguntas del conjunto independiente anterior | 22/24 (91.67 %) | 22/24 (91.67 %) |

La pregunta «Quiero pronosticar huracanes» pasó de `filtrar_modalidad` a `explorar_area`. El conjunto de 40 preguntas se utilizó para seleccionar la mejora, por lo que **su resultado no constituye una evaluación final independiente**. Estos porcentajes miden **clasificación de intenciones**, no exactitud global del asistente.

Archivos relevantes: `datos/intenciones_entrenamiento.csv`, `datos/intenciones_entrenamiento_original_80.csv`, `datos/pruebas_intenciones_nuevas.csv`, `motor_ia/clasificador.py`, `motor_ia/interpretar_consulta.py` y `scripts/comparar_intenciones_actualizado.py`.

### Recuperación semántica, cobertura temática y alternativas afines

El sistema utiliza el modelo preentrenado `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` para comparar una pregunta con los **588 nombres de programas** recuperados de PostgreSQL.

La búsqueda incorpora una comprobación de **cobertura temática**: antes de mostrar resultados, revisa si hay programas cuyos títulos contienen indicios explícitos del área. Así se evita presentar coincidencias engañosas, como Gastronomía para una pregunta sobre planetas.

Cuando no existe cobertura directa, el asistente puede **ofrecer** explorar áreas generales afines. Solo tras la confirmación del estudiante (`sí`), consulta las ofertas reales de esas carreras en PostgreSQL. **No presenta las áreas afines como equivalentes a la especialidad solicitada**.

Ejemplo probado con «Quiero pronosticar huracanes»:

1. Identifica el interés en **Meteorología** y explica que no encontró un programa cuyo nombre indique directamente esa especialidad.
2. Pregunta si el estudiante desea explorar carreras afines.
3. Tras responder «Sí», recupera las ofertas registradas de **Ingeniería Física** (Universidad Iberoamericana Ciudad de México) y **Matemáticas Aplicadas** (Instituto Tecnológico Autónomo de México); ambas aparecieron como escolarizadas en la prueba realizada.
4. Permite un seguimiento como «¿Y cuáles de esas opciones son mixtas?». En la prueba no aparecieron ofertas mixtas para esas alternativas.

Estas alternativas se eligieron **por reglas académicas auxiliares**, no mediante una comprobación de planes de estudio. Los resultados dependen del catálogo de 2021.

Archivos relevantes: `motor_ia/busqueda_semantica.py`, `motor_ia/recuperacion_semantica.py`, `motor_ia/validacion_cobertura_tematica.py`, `motor_ia/afinidades_academicas.py` y `motor_ia/contexto.py`.

### Generación de respuestas y contexto

Se incorporó `motor_ia/generador_respuestas.py`, que redacta mensajes a partir de los nombres de instituciones, programas, planteles y modalidades recuperados de PostgreSQL. **No utiliza un segundo modelo generativo** ni inventa universidades u ofertas para completar respuestas.

`app.py` conserva el contexto de la sesión para:

- Consultar modalidades de programas previamente encontrados por MiniLM.
- Filtrar opciones afines aceptadas por el estudiante.
- Realizar búsquedas tradicionales por carrera o institución.
- Cambiar de tema sin conservar filtros que ya no corresponden.

El modo técnico puede activarse mediante `MODO_DIAGNOSTICO = True` en `app.py` para mostrar la intención clasificada y su puntuación.

### Pruebas realizadas

Se ejecutaron **6 pruebas unitarias satisfactorias** mediante `pytest` para las reglas de afinidad y la generación de respuestas. También se verificó manualmente, en una sesión real con PostgreSQL, la siguiente secuencia conversacional:

| Consulta o acción | Resultado observado |
|---|---|
| Quiero pronosticar huracanes | Reconoce Meteorología y ofrece consultar áreas afines |
| Sí | Muestra Ingeniería Física y Matemáticas Aplicadas registradas en el catálogo |
| ¿Y cuáles de esas opciones son mixtas? | No encuentra ofertas para ese filtro |
| Me gustaría desarrollar videojuegos y programar mundos virtuales | Recupera cinco programas relacionados con videojuegos |
| ¿Y cuáles de esas opciones son mixtas? | Recupera dos ofertas mixtas de Instituto SAE |
| ¿Qué carreras ofrece la Universidad ICEL? | Recupera 313 ofertas |
| ¿Y cuáles son mixtas? | Recupera 75 ofertas mixtas de ICEL |

Estas pruebas confirman **los escenarios ejecutados**, pero **no garantizan el comportamiento ante cualquier consulta**. La evaluación integral del asistente permanece pendiente.

Ejecutar las pruebas unitarias desde la raíz del proyecto:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_afinidades.py -v
```
Ejecutar el asistente:
```powershell
.\.venv\Scripts\python.exe app.py
```
### Instalación manual de MiniLM

Los pesos del modelo **no se incluyen en GitHub**. La carpeta `modelos_ia/` está excluida mediante `.gitignore` porque contiene una copia descargable de un modelo preentrenado y archivos de gran tamaño. El código Python que emplea MiniLM **sí forma parte del proyecto**.

En Windows PowerShell, desde la raíz del repositorio y con el entorno virtual configurado:
```powershell
.\.venv\Scripts\python.exe -m pip install sentence-transformers
.\.venv\Scripts\python.exe motor_ia\12_probar_embeddings.py
```
La segunda instrucción descarga el modelo desde Hugging Face en la primera ejecución y lo guarda en `modelos_ia/minilm/`. Después `app.py` lo carga localmente. También se requiere PostgreSQL configurado con la base de datos `oferta_educativa` y las dependencias del proyecto.

**Mejora pendiente:** incorporar la descarga automática del modelo desde `app.py` cuando no exista una copia local. Por ahora el paso manual sigue siendo necesario.

### Limitaciones y siguiente etapa

- El catálogo corresponde a **abril de 2021** y no comprueba vigencia actual.
- La detección de temas y las afinidades utilizan reglas auxiliares con cobertura limitada; podrían excluir carreras afines cuyos títulos no revelen su relación con la consulta.
- Las recomendaciones son **orientativas**, no equivalencias académicas ni garantía de formación profesional.
- Las métricas del clasificador no sustituyen la evaluación integral de recuperación, pertinencia y conversación.
- Queda pendiente la evaluación sistemática con nuevas preguntas, el análisis de errores y el cierre de documentación y presentación.

La etapa 3 cuenta con una **versión funcional para los escenarios probados**; el siguiente trabajo corresponde a la **evaluación integral de la etapa 4**.

**Incidencia observada al cierre de esta versión:** saludos y despedidas informales pueden recibir el mensaje genérico de falta de tema académico. Es una limitación de interacción pendiente de revisar; no invalida los casos de búsqueda académica comprobados.
