-------------------------------
--Lionel-A
--SIDT IGN 07/2015
-------------------------------

------
-- for TrafiPollu soft.
-- update def_zone_test a partir d'un polygone transmis

-- url: http://postgis.org/docs/ST_Transform.html
-- url: http://postgis.net/docs/Find_SRID.html

UPDATE street_amp.def_zone_test
SET geom = ST_Transform(
    ST_GeomFromText(%(gPolygonWkt)s, %(gPolygonSRID)s),
    Find_SRID('street_amp', 'def_zone_test', 'geom')
)
WHERE
  (
    gid = 2
    AND
    NOT ST_Equals(ST_Transform(
                      ST_GeomFromText(%(gPolygonWkt)s, %(gPolygonSRID)s),
                      Find_SRID('street_amp', 'def_zone_test', 'geom')
                  ),
                  street_amp.def_zone_test.geom
    )
  );

-- SET search_path TO street_amp, bdtopo_topological, bdtopo,topology,public;
--         set client_min_messages to  WARNING;
--
--
-- WITH input_geom AS (
--         SELECT  array_agg(ed.edge_id) as i_edges
--             FROM bdtopo_topological.edge_data AS ed,
--                 ST_GeomFromText(%(gPolygonWkt)s, %(gPolygonSRID)s) AS poly
--             WHERE ST_Intersects(ed.geom, ST_Transform(poly, Find_SRID('bdtopo_topological', 'edge_data', 'geom'))) = TRUE
--
--     )
-- SELECT r.*
-- FROM input_geom , street_amp.rc_generate_street_amp_result(i_edges)  as r;

-- si erreur
-- faire
-- SELECT pg_advisory_unlock_all() ;