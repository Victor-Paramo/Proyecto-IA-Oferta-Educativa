SELECT
    i.id_institucion,
    i.nombre AS institucion,
    p.id_plantel,
    p.nombre AS plantel,
    COUNT(o.id_oferta) AS ofertas
FROM catalogo.institucion i
JOIN catalogo.plantel p
    ON p.id_institucion = i.id_institucion
LEFT JOIN catalogo.oferta_educativa o
    ON o.id_plantel = p.id_plantel
WHERE i.nombre ILIKE '%TECNOL%'
  AND i.nombre ILIKE '%M%XICO%'
GROUP BY
    i.id_institucion,
    i.nombre,
    p.id_plantel,
    p.nombre
ORDER BY i.nombre, p.id_plantel;