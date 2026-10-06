\# Proyecto de Inteligencia Artificial – Oferta Educativa



Proyecto desarrollado para la asignatura de Inteligencia Artificial.



\## Objetivo



Desarrollar un sistema para procesar, estructurar y analizar información de la oferta educativa, con énfasis inicial en las licenciaturas disponibles en la Ciudad de México.



El proyecto utiliza como fuente archivos PDF que contienen registros oficiales de instituciones y programas educativos.



\## Proceso realizado



Hasta el momento se han desarrollado las siguientes etapas:



1\. Extracción automática de tablas desde archivos PDF.

2\. Conversión de los registros extraídos a formato JSON.

3\. Integración de los registros procedentes de los diferentes archivos.

4\. Identificación de registros sospechosos y errores producidos durante la extracción.

5\. Revisión de casos particulares contra los documentos originales.

6\. Limpieza y normalización inicial de los datos.

7\. Generación de un archivo JSON limpio para las siguientes etapas del proyecto.



\## Datos obtenidos



Actualmente se procesaron:



\- 27,054 registros nacionales.

\- 5,312 registros correspondientes a Ciudad de México.

\- 2,810 registros de licenciaturas en Ciudad de México.



Después del proceso de limpieza, los niveles de estudios reconocidos son:



\- Licenciatura

\- Maestría

\- Especialidad

\- Doctorado

\- Técnico Superior Universitario

\- Profesional Asociado



\## Estructura del proyecto



\- `PDFs/`: documentos utilizados como fuente de información.

\- `datos/`: archivos JSON obtenidos durante la extracción, análisis y limpieza.

\- `scripts/`: programas de Python utilizados para procesar la información.



\## Tecnologías utilizadas



\- Python 3.12

\- pdfplumber

\- JSON

\- PostgreSQL (para la etapa de almacenamiento y consulta)



\## Estado actual



Actualmente se terminó la extracción y una primera etapa de limpieza de los datos.



La siguiente etapa consiste en diseñar el modelo Entidad-Relación, realizar la normalización del modelo relacional e implementar la base de datos en PostgreSQL.

