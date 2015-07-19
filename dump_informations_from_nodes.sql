-------------------------------
--Lionel-A
--SIDT IGN 04/2015
-------------------------------

------
-- for TrafiPollu soft.
-- retrieve (dump) 'informations' from nodes selected in QGIS client

SELECT
  node_id,
  edges_ids,
  ST_AsEWKB(bt_node.geom) AS wkb_geom
FROM (SELECT
        nodes_selected.node_id    AS node_id,
        array_agg(oepnp.edge_id1) AS edges_ids
      FROM
        bdtopo_topological.ordered_edges_per_node_pair AS oepnp
        JOIN
        test.nodes_selected AS nodes_selected
          ON
            nodes_selected.node_id = oepnp.node_id
      GROUP BY nodes_selected.node_id
     ) AS result
  NATURAL JOIN bdtopo_topological.node AS bt_node
WHERE bt_node.node_id = result.node_id