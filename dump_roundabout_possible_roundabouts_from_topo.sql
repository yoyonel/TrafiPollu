-------------------------------
--Lionel-A
--SIDT IGN 2015/12/21
-------------------------------

------
-- for TrafiPollu soft.

SET search_path TO analysis_roundabout_bdtopo, rc_lib, topology, PUBLIC;

WITH edges_selected AS (
    SELECT
      ed.left_face as gid
      ,ed.*
    FROM analysis_roundabout_bdtopo.possible_roundabouts_from_topo as arbprtt
    , bdtopo_topological.edge_data AS ed
    WHERE
      ed.left_face = arbprtt.face_id OR ed.right_face = arbprtt.face_id
)
SELECT
  es_gid        AS id  
  ,ST_Centroid(ra.face_geom) AS wkb_centroid  -- geometrie du centre du rond-point  
  ,es_list_nodes AS list_nodes    -- list des (id des) nodes (BDTopo) dans le rond-point
  ,es_list_edges AS list_edges    -- list des (id des) edges (BDTopo) dans le rond-point
FROM (SELECT
        gid                   AS es_gid
        ,array_agg(start_node) AS es_list_nodes
        ,array_agg(edge_id)    AS es_list_edges
      FROM edges_selected
      GROUP BY es_gid
     ) AS results_agg
  NATURAL JOIN analysis_roundabout_bdtopo.possible_roundabouts_from_topo AS ra
WHERE ra.face_id = es_gid