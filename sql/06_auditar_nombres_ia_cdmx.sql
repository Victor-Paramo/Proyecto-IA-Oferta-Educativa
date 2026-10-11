-- Proyecto IA - Oferta Educativa
-- Auditoria de nombres para el recomendador de licenciaturas CDMX
-- PostgreSQL 16 | SOLO LECTURA | Ejecutar conectado a oferta_educativa
-- No certifica que un nombre sea correcto; identifica candidatos a revision.

\echo '============================================================'
\echo 'AUDITORIA DE NOMBRES - LICENCIATURAS CDMX'
\echo '============================================================'

-- Trabajamos sobre registros de ORIGEN que efectivamente cumplen el alcance.
-- Para evitar problemas de acentos de la consola, construimos MEXICO con CHR(201).
CREATE TEMP VIEW auditoria_ia_cdmx AS
SELECT
    r.id_registro,
    r.datos_json->>'institucion' AS institucion_original,
    r.datos_json->>'programa' AS programa_original,
    v.estado_revision,
    i.id_institucion,
    i.nombre AS institucion_catalogo,
    p.id_plantel,
    p.nombre AS plantel_catalogo,
    pr.id_programa,
    pr.nombre AS programa_catalogo,
    m.nombre AS modalidad
FROM origen.registro_origen r
LEFT JOIN origen.vinculo_registro v ON v.id_registro = r.id_registro
LEFT JOIN catalogo.oferta_educativa o ON o.id_oferta = v.id_oferta
LEFT JOIN catalogo.plantel p ON p.id_plantel = o.id_plantel
LEFT JOIN catalogo.institucion i ON i.id_institucion = p.id_institucion
LEFT JOIN catalogo.programa_academico pr ON pr.id_programa = o.id_programa
LEFT JOIN catalogo.modalidad m ON m.id_modalidad = o.id_modalidad
WHERE r.datos_json->>'estado' = 'CIUDAD DE M' || CHR(201) || 'XICO'
  AND r.datos_json->>'nivel_estudios' = 'LICENCIATURA';

\echo ''
\echo '1) Cobertura e integridad de nombres esenciales'
SELECT
    COUNT(*) AS registros_cdmx_licenciatura,
    COUNT(*) FILTER (WHERE id_institucion IS NULL OR id_programa IS NULL OR modalidad IS NULL) AS sin_vinculo_esencial,
    COUNT(*) FILTER (WHERE NULLIF(BTRIM(institucion_catalogo), '') IS NULL) AS institucion_vacia,
    COUNT(*) FILTER (WHERE NULLIF(BTRIM(programa_catalogo), '') IS NULL) AS programa_vacio,
    COUNT(*) FILTER (WHERE plantel_catalogo IS NULL OR BTRIM(plantel_catalogo) = '') AS plantel_no_especificado,
    COUNT(DISTINCT id_institucion) AS instituciones_con_ofertas,
    COUNT(DISTINCT id_programa) AS programas_con_ofertas
FROM auditoria_ia_cdmx;

\echo ''
\echo '2) Instituciones con nombres sospechosos: cantidad e impacto'
-- Indicadores de revision, NO errores comprobados.
WITH candidatos AS (
    SELECT DISTINCT id_institucion, institucion_catalogo
    FROM auditoria_ia_cdmx
    WHERE id_institucion IS NOT NULL
), marcas AS (
    SELECT *,
      (institucion_catalogo ~ '[()]' OR institucion_catalogo ~* '\m(CAMPUS|PLANTEL|SEDE)\M') AS posible_sede_en_nombre,
      (institucion_catalogo ~ '[()]' AND (
        instituCion_catalogo LIKE '%(' OR institucion_catalogo LIKE '%)(' OR
        LENGTH(institucion_catalogo) - LENGTH(REPLACE(institucion_catalogo, '(', '')) <> LENGTH(institucion_catalogo) - LENGTH(REPLACE(institucion_catalogo, ')', ''))
      )) AS parentesis_incompletos,
      (institucion_catalogo ~* '(^|[[:space:]])(CAMPUS|PLANTEL|DEL|DE|LA|EL)$') AS final_incompleto,
      (institucion_catalogo ~* 'TE\(|CEPNLT|PCLEANNT|EPSETCU|EOSTRUED|REOC ADTEE|TECVN') AS texto_contaminado
    FROM candidatos
)
SELECT
 COUNT(*) AS instituciones_unicas,
 COUNT(*) FILTER (WHERE posible_sede_en_nombre) AS con_indicador_sede,
 COUNT(*) FILTER (WHERE parentesis_incompletos OR final_incompleto OR texto_contaminado) AS sospecha_fuerte,
 COUNT(*) FILTER (WHERE posible_sede_en_nombre AND NOT (parentesis_incompletos OR final_incompleto OR texto_contaminado)) AS revisar_contexto
FROM marcas;

\echo ''
\echo '3) Instituciones candidatas (hasta 80), con registros afectados'
WITH grupos AS (
 SELECT id_institucion, institucion_catalogo,
        COUNT(DISTINCT id_registro) AS registros_licenciatura,
        COUNT(DISTINCT id_plantel) AS planteles
 FROM auditoria_ia_cdmx
 WHERE id_institucion IS NOT NULL
 GROUP BY id_institucion, institucion_catalogo
), marcados AS (
 SELECT *,
  CASE
   WHEN institucion_catalogo ~* 'TE\(|CEPNLT|PCLEANNT|EPSETCU|EOSTRUED|REOC ADTEE|TECVN'
     OR institucion_catalogo ~* '(^|[[:space:]])(CAMPUS|PLANTEL|DEL|DE|LA|EL)$'
     OR (LENGTH(institucion_catalogo)-LENGTH(REPLACE(institucion_catalogo,'(',''))) <>
         (LENGTH(institucion_catalogo)-LENGTH(REPLACE(institucion_catalogo,')','')))
   THEN 'ALTA - revisar PDF'
   WHEN institucion_catalogo ~* '\m(CAMPUS|PLANTEL|SEDE)\M' OR institucion_catalogo ~ '[()]'
   THEN 'MEDIA - posible sede en nombre'
   ELSE NULL END AS motivo
 FROM grupos
)
SELECT id_institucion, institucion_catalogo AS institucion, registros_licenciatura, planteles, motivo
FROM marcados
WHERE motivo IS NOT NULL
ORDER BY CASE WHEN motivo LIKE 'ALTA%' THEN 0 ELSE 1 END, registros_licenciatura DESC, id_institucion
LIMIT 80;

\echo ''
\echo '4) Programas con nombres potencialmente incompletos/contaminados'
-- No marcamos el prefijo EN: es comun y legitimo en esta fuente.
WITH programas AS (
 SELECT id_programa, programa_catalogo, COUNT(DISTINCT id_registro) AS registros
 FROM auditoria_ia_cdmx
 WHERE id_programa IS NOT NULL
 GROUP BY id_programa, programa_catalogo
)
SELECT id_programa, programa_catalogo AS programa, registros
FROM programas
WHERE programa_catalogo ~ '[()]'
   OR programa_catalogo ~* '(^|[[:space:]])(DE|DEL|LA|EL|EN|Y|PARA|CON)$'
   OR programa_catalogo ~* 'TE\(|CEPNLT|PCLEANNT|EPSETCU|EOSTRUED|REOC ADTEE|TECVN'
   OR LENGTH(programa_catalogo) < 5
ORDER BY registros DESC, id_programa
LIMIT 80;

\echo ''
\echo '5) Nombres originales distintos para una misma institucion de catalogo'
-- Puede ser normal (varios campus), pero ayuda a revisar fusiones.
SELECT id_institucion, institucion_catalogo AS institucion,
       COUNT(DISTINCT institucion_original) AS variantes_originales,
       COUNT(DISTINCT id_registro) AS registros
FROM auditoria_ia_cdmx
WHERE id_institucion IS NOT NULL
GROUP BY id_institucion, institucion_catalogo
HAVING COUNT(DISTINCT institucion_original) > 1
ORDER BY variantes_originales DESC, registros DESC
LIMIT 30;

DROP VIEW auditoria_ia_cdmx;
\echo ''
\echo 'FIN. Ninguna tabla permanente fue modificada.'
