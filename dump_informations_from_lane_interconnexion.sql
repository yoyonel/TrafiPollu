-------------------------------
--Lionel-A
--SIDT IGN 06/2015
-------------------------------

------
-- for TrafiPollu soft.
-- retrieve (dump) 'informations' about lanes interconnexions from nodes selected in QGIS client

SELECT
  DISTINCT
  nodes_selected.node_id         AS str_node_id,

  vrli.edge_id1                  AS str_edge_id1,
  vrli.edge_id2                  AS str_edge_id2,
  vrli.lane_ordinality1          AS str_lane_ordinality1,
  vrli.lane_ordinality2          AS str_lane_ordinality2,

  ST_AsEWKB(vrli.interconnexion) AS wkb_interconnexion
FROM
  street_amp.visu_result_lane_interconnexion AS vrli
  JOIN
  test.nodes_selected AS nodes_selected
    ON
      nodes_selected.node_id = vrli.node_id
WHERE
  vrli.connecting = TRUE  -- seules les interconnexions connectees nous interessent
--ORDER BY str_node_id, str_array_edge_id1, str_array_edge_id2, str_array_lane_ordinality1, str_array_lane_ordinality2
