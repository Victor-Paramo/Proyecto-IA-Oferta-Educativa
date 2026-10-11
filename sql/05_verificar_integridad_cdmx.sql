-- Proyecto IA - Oferta Educativa
-- Verificacion posterior a limpiezas de catalogo (solo lectura).
-- Ejecutar conectado a la base oferta_educativa.
-- No requiere cambios en la codificacion de la terminal: nombres sin acentos.

SELECT
    (SELECT COUNT(*) FROM origen.registro_origen) AS registros_nacionales,
    (SELECT COUNT(*) FROM catalogo.institucion) AS instituciones,
    (SELECT COUNT(*) FROM catalogo.plantel) AS planteles,
    (SELECT COUNT(*) FROM catalogo.oferta_educativa) AS ofertas,
    (SELECT COUNT(*) FROM catalogo.autorizacion) AS autorizaciones,
    (SELECT COUNT(*) FROM origen.vinculo_registro) AS vinculos;

-- Comprobar los vinculos referentes a licenciaturas de CDMX.
WITH alcance AS (
    SELECT r.id_registro
    FROM origen.registro_origen r
    WHERE r.datos_json->>'estado' = 'CIUDAD DE M' || chr(201) || 'XICO'
      AND r.datos_json->>'nivel_estudios' = 'LICENCIATURA'
)
SELECT
    COUNT(*) AS registros_cdmx_licenciatura,
    COUNT(v.id_registro) AS vinculados,
    COUNT(*) FILTER (WHERE v.id_registro IS NULL) AS sin_vinculo,
    COUNT(*) FILTER (WHERE v.estado_revision = 'REVISAR') AS por_revisar,
    COUNT(*) FILTER (WHERE v.id_registro IS NOT NULL AND o.id_oferta IS NULL) AS sin_oferta
FROM alcance a
LEFT JOIN origen.vinculo_registro v ON v.id_registro = a.id_registro
LEFT JOIN catalogo.oferta_educativa o ON o.id_oferta = v.id_oferta;

-- Localizar instituciones que tienen nombres con posible sede incorporada.
-- Un resultado es un CANDIDATO de revision, no un duplicado demostrado.
SELECT
    i.id_institucion,
    i.nombre,
    COUNT(DISTINCT p.id_plantel) AS planteles,
    COUNT(DISTINCT o.id_oferta) AS ofertas
FROM catalogo.institucion i
LEFT JOIN catalogo.plantel p ON p.id_institucion = i.id_institucion
LEFT JOIN catalogo.oferta_educativa o ON o.id_plantel = p.id_plantel
WHERE i.nombre ILIKE '%CAMPUS%'
   OR i.nombre ILIKE '%PLANTEL%'
   OR i.nombre LIKE '%(%'
GROUP BY i.id_institucion, i.nombre
ORDER BY ofertas DESC, i.id_institucion;
