-------------------------------
--Lionel-A
--SIDT IGN 04/2015
-------------------------------

------
-- for TrafiPollu soft.
-- retrieve (dump) 'informations' from edges selected in QGIS client
-- url: http://www.postgis.org/docs/ST_AsEWKB.html

SELECT
--
  DISTINCT
  edges.edge_id                       AS edge_id,
  edges.ign_id                        AS ign_id,
  edges.start_node                    AS start_node,
  edges.end_node                      AS end_node,
  axis.road_width                     AS road_width,
  axis.lane_number                    AS lane_number,
  names_edges.nom_rue_g               AS nom_rue_g,
  names_edges.nom_rue_d               AS nom_rue_d,
  ST_AsEWKB(edges.geom)               AS wkb_edge_center_axis,
  ST_AsEWKB(axis.intersection_limit1) AS wkb_amont,
  ST_AsEWKB(axis.intersection_limit2) AS wkb_aval
FROM test.edges_selected AS edges
  INNER JOIN street_amp.visu_result_axis AS axis ON edges.edge_id = axis.edge_id
  INNER JOIN test.names_edges_selected AS names_edges ON edges.ign_id = names_edges.ign_id
ORDER BY edges.edge_id
