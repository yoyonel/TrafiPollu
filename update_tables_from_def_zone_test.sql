DROP VIEW IF EXISTS test.names_edges_selected;
DROP VIEW IF EXISTS test.edges_selected;
CREATE VIEW test.edges_selected
AS (

  SELECT
    edge_id,
    ign_id,
    start_node,
    end_node,
    ed.geom
  FROM
    bdtopo_topological.edge_data AS ed
    , street_amp.def_zone_test AS dzt
  WHERE
    (
      ST_Intersects(ST_Transform(dzt.geom, Find_SRID('bdtopo_topological', 'edge_data', 'geom')), ed.geom)
      OR
      ST_Contains(ST_Transform(dzt.geom, Find_SRID('bdtopo_topological', 'edge_data', 'geom')), ed.geom)
    )
    AND
    -- s'assure que les elements selectionnes sont (updatés) dans SG3 (visul_result_axis)
    EXISTS(SELECT
             1
           FROM street_amp.visu_result_axis AS v_r_a
           WHERE v_r_a.edge_id = ed.edge_id)
  ORDER BY edge_id

);

CREATE VIEW test.names_edges_selected
AS (
  SELECT
    test.edges_selected.ign_id,
    road.nom_rue_g,
    road.nom_rue_d
  FROM test.edges_selected
    LEFT OUTER JOIN bdtopo.road ON (test.edges_selected.ign_id = road.id)
  ORDER BY test.edges_selected.ign_id
);


DROP VIEW IF EXISTS test.nodes_selected;
CREATE VIEW test.nodes_selected
AS (
  SELECT
    DISTINCT
    node_id
  FROM
    bdtopo_topological.node AS n
    , street_amp.def_zone_test AS dzt
  WHERE
    (
      ST_Intersects(ST_Transform(dzt.geom, Find_SRID('bdtopo_topological', 'node', 'geom')), n.geom)
      OR
      ST_Contains(ST_Transform(dzt.geom, Find_SRID('bdtopo_topological', 'node', 'geom')), n.geom)
    )
    AND
    -- s'assure que les elements selectionnes sont (updatés) dans SG3 (visul_result_axis)
    EXISTS(SELECT
             1
           FROM street_amp.visu_result_intersection AS v_r_i
           WHERE v_r_i.node_id = n.node_id)
  ORDER BY node_id
);
