# Proyecto de Inteligencia Artificial – Oferta Educativa

Proyecto desarrollado para la asignatura de Inteligencia Artificial.

## Objetivo

Desarrollar un sistema para procesar, estructurar y analizar información de la oferta educativa, con énfasis inicial en las licenciaturas disponibles en la Ciudad de México.

El proyecto utiliza como fuente documentos PDF con registros oficiales de instituciones y programas educativos.

La arquitectura está preparada para ampliar posteriormente la cobertura al resto de México.

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

## Estado actual de PostgreSQL

Después de la carga inicial y las primeras correcciones, se obtuvieron los siguientes resultados:

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

Los 2,810 vínculos se conservan en estado `REVISAR` mientras continúa la validación de identidades institucionales y autorizaciones.

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

La validación de los casos restantes continúa pendiente.

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
- `limpieza_catalogo_cdmx_historial.md`: historial de correcciones del catálogo.
- `.gitignore`: configuración de archivos excluidos del control de versiones.
- `README.md`: documentación del proyecto.

## Tecnologías utilizadas

- Python 3.12
- pdfplumber
- JSON
- PostgreSQL 16
- psycopg2-binary
- Git y GitHub

## Estado del proyecto y siguientes etapas

**La extracción, la carga documental, el diseño de la base de datos y la primera integración de licenciaturas de CDMX están completados.**

Actualmente se trabaja en mejorar la calidad de las correspondencias institucionales y de los planteles, conservando los datos originales.

Las próximas etapas son:

1. Continuar la limpieza controlada de instituciones y planteles.
2. Revisar autorizaciones y registros que presentan inconsistencias.
3. Consolidar y validar las consultas académicas.
4. Desarrollar la interfaz de búsqueda de licenciaturas de CDMX.
5. Incorporar las funcionalidades de Inteligencia Artificial.
6. Realizar pruebas funcionales y documentar los resultados.
7. Ampliar posteriormente la cobertura a nivel nacional.

**El alcance actual de la aplicación continúa limitado a las licenciaturas de Ciudad de México.**

## Motor de Inteligencia Artificial

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

El conjunto de entrenamiento contiene 80 preguntas etiquetadas, distribuidas entre cuatro categorías:

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

Se seleccionó provisionalmente regresión logística para la integración inicial, debido a su desempeño y facilidad de interpretación.

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

### Estado actual

La primera integración del motor de IA permite clasificar la intención del usuario y reconocer instituciones, programas y modalidades a partir de consultas en español.

Todavía están pendientes las funciones de recuperación de ofertas educativas, la búsqueda semántica, la gestión del contexto conversacional y la generación de respuestas fundamentadas.

**Nota:** Los datos oficiales utilizados provienen de documentos de la SEP con información actualizada al 30 de abril de 2021. Los resultados deben interpretarse considerando esa limitación temporal.