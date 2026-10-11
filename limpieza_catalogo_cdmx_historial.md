# Historial de depuracion del catalogo de licenciaturas de CDMX

Base de datos: `oferta_educativa` (PostgreSQL). Alcance normalizado: licenciaturas de CDMX; la capa `origen` conserva 27,054 registros nacionales.

## Operaciones realizadas durante la sesion

Las siguientes operaciones **ya se ejecutaron manualmente en PostgreSQL**. Este documento es un registro de trabajo, **no una migracion SQL para volver a ejecutar**. Los identificadores corresponden a esa instancia y pueden variar en instalaciones nuevas.

| Grupo | Institucion conservada | Reasignaciones y cambios | Registros institucionales eliminados |
| --- | --- | --- | --- |
| Tecnologico de Monterrey | `id_institucion=16` | Planteles provisionales 218 y 219 consolidados en 49 (Ciudad de Mexico); 220 y 221 en 50 (Santa Fe); 13 ofertas trasladadas; planteles 218-221 eliminados despues de quedar vacios | 176, 177, 178, 179 |
| UNITEC | `id_institucion=268` | Planteles 312, 313, 314 y 315 vinculados a 268; nombres Azcapotzalco, Cuitlahuac, Marina y Sur; plantel 311 sin nombre de sede | 269, 270, 271, 272 |
| Universidad de Londres | `id_institucion=212` | Planteles 255-261 vinculados a 212 y nombrados Doctores, Insurgentes Sur, Roma II, III, IV, V y Roma; 254 sin sede identificada | 213-219 |
| Universidad Insurgentes | `id_institucion=3` | Planteles 278-284 vinculados a 3 y nombrados segun su denominacion original, sin fusionar las variantes | 235-241 |
| Universidad La Salle | `id_institucion=248` | Planteles 292-295 vinculados a 248 y nombrados Condesa, Hill, Pedregal y Tlalpan | 249-252 |
| Universidad Panamericana | `id_institucion=259` | Planteles 303 y 304 vinculados a 259 y nombrados Rodin y Santa Fe II | 260, 261 |

**Ultimos totales observados antes del COMMIT final de las tres universidades:** 258 instituciones, 326 planteles, 2,616 ofertas, 2,740 autorizaciones y 2,810 vinculos documentales. Confirmar el COMMIT y reejecutar la consulta de integridad para registrar el estado persistido.

## Criterios usados

- No modificar los 27,054 registros de `origen.registro_origen`.
- No fusionar planteles por nombres parecidos sin evidencia; conservamos variantes como Roma II y Roma III.
- Reasignar las claves foraneas antes de retirar filas de catalogo sin referencias.
- Comprobar los recuentos de ofertas, autorizaciones y vinculos antes de confirmar transacciones.
- Los 2,810 vinculos siguen con `estado_revision='REVISAR'`; los recuentos correctos **no equivalen a validacion documental completa**.

## Siguiente lote

Ejecutar `sql/05_verificar_integridad_cdmx.sql`. Revisar sus instituciones candidatas y los registros originales de CDMX para aprobar correspondencias. Aplicar correcciones futuras en una migracion nueva con condiciones previas, transaccion y controles posteriores; no volver a ejecutar los `UPDATE`/`DELETE` historicos por ID.
