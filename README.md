# Proyecto de Inteligencia Artificial – Oferta Educativa

Proyecto desarrollado para la asignatura de Inteligencia Artificial.

## Objetivo

Desarrollar un sistema para procesar, estructurar y analizar información de la oferta educativa, con énfasis inicial en las licenciaturas disponibles en la Ciudad de México.

El proyecto utiliza como fuente archivos PDF que contienen registros oficiales de instituciones y programas educativos.

## Proceso realizado

Hasta el momento se han desarrollado las siguientes etapas:

1. Extracción automática de tablas desde archivos PDF.
2. Conversión de los registros extraídos a formato JSON.
3. Integración de los registros procedentes de los diferentes archivos.
4. Identificación de registros sospechosos y errores producidos durante la extracción.
5. Revisión de casos particulares contra los documentos originales.
6. Limpieza y normalización inicial de los datos.
7. Generación de un archivo JSON limpio para las siguientes etapas del proyecto.
8. Auditoría estructural para analizar dependencias funcionales, duplicados y relaciones entre atributos.
9. Elaboración del modelo Entidad–Relación (MER).
10. Elaboración de una propuesta de modelo relacional para PostgreSQL.

## Datos obtenidos

Actualmente se procesaron:

- **27,054 registros nacionales.**
- **5,312 registros correspondientes a Ciudad de México.**
- **2,810 registros de licenciaturas en Ciudad de México.**

Después del proceso de limpieza, los niveles de estudios reconocidos son:

- Licenciatura
- Maestría
- Especialidad
- Doctorado
- Técnico Superior Universitario
- Profesional Asociado

Los registros se encuentran consolidados en el archivo `oferta_educativa_limpia.json`.

## Diseño de la base de datos

Se elaboraron los modelos conceptual y relacional para organizar la información educativa, reducir redundancias y preparar su almacenamiento en PostgreSQL.

La arquitectura propuesta utiliza una sola base de datos denominada `oferta_educativa`, organizada en dos esquemas:

- **`catalogo`:** destinado a almacenar instituciones, planteles, estados, niveles académicos, programas, modalidades, ofertas educativas y autorizaciones.
- **`origen`:** destinado a conservar los registros extraídos de los documentos PDF y su procedencia.

Ambos esquemas se relacionan mediante claves foráneas, permitiendo asociar la información normalizada con los registros originales.

### Modelo Entidad–Relación (MER)

El modelo conceptual identifica las entidades principales, sus atributos, relaciones y cardinalidades.

![Modelo Entidad–Relación](diagramas/modelo_entidad_relacion.png)

### Modelo relacional

El modelo relacional representa las tablas propuestas, sus atributos, claves primarias (PK), claves foráneas (FK) y restricciones de unicidad (UQ).

![Modelo relacional](diagramas/modelo_relacional.png)

### Normalización

El diseño contempla la aplicación de los principios de Primera Forma Normal (1FN), Segunda Forma Normal (2FN) y Tercera Forma Normal (3FN).

La separación de instituciones, planteles, programas, niveles académicos y modalidades busca reducir la redundancia y evitar anomalías de inserción, actualización y eliminación.

Adicionalmente, la capa `origen` permitirá conservar los datos extraídos para facilitar la revisión de inconsistencias y mantener la trazabilidad documental.

La validación definitiva de la normalización y de las restricciones se realizará durante la implementación y las pruebas de carga.

## Estructura del proyecto

- `PDFs/`: documentos utilizados como fuente de información.
- `datos/`: archivos JSON obtenidos durante la extracción, análisis, limpieza y auditoría.
- `scripts/`: programas de Python utilizados para procesar la información.
- `diagramas/`: representaciones gráficas de los modelos conceptual y relacional.
- `.gitignore`: configuración de exclusiones para Git.
- `README.md`: documentación general del proyecto.

## Tecnologías utilizadas

- Python 3.12
- pdfplumber
- JSON
- PostgreSQL (para la etapa de almacenamiento y consulta)
- Git y GitHub (control de versiones)

## Estado actual

Se completaron la extracción de datos, la consolidación de los registros, una primera etapa de limpieza y la auditoría estructural.

También se elaboraron los diagramas del modelo Entidad–Relación y del modelo relacional propuesto.

Las siguientes etapas consisten en:

1. Revisar las reglas de identificación de instituciones, planteles y ofertas educativas.
2. Implementar los esquemas y las tablas en PostgreSQL.
3. Cargar los registros originales conservando su procedencia.
4. Transformar e integrar los datos en las tablas normalizadas.
5. Verificar las restricciones de integridad y la consistencia de las relaciones.
6. Desarrollar las consultas y funcionalidades del sistema de Inteligencia Artificial.

La prioridad continúa siendo la oferta de licenciaturas en Ciudad de México, manteniendo una arquitectura que permita incorporar posteriormente información del resto del país.