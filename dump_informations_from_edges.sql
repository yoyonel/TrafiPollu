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
  DISTINCT edges.edge_id                AS str_edge_id,
  edges.ign_id                        AS str_ign_id,
  ST_AsEWKB(edges.geom)               AS wkb_edge_center_axis,
  edges.start_node                    AS ui_start_node,
  edges.end_node                      AS ui_end_node
  ,ST_AsEWKB(axis.intersection_limit1)  AS wkb_amont,
  ST_AsEWKB(axis.intersection_limit2) AS wkb_aval,
  axis.road_width                     AS f_road_width,
  axis.lane_number                    AS ui_lane_number,
  names_edges.nom_rue_g               AS str_nom_rue_g,
  names_edges.nom_rue_d               AS str_nom_rue_d
FROM test.edges_selected AS edges
  INNER JOIN street_amp.visu_result_axis AS axis ON edges.edge_id = axis.edge_id
  INNER JOIN test.names_edges_selected AS names_edges ON edges.ign_id = names_edges.ign_id
ORDER BY edges.edge_id
