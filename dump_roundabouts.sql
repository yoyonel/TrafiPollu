-------------------------------
--Lionel-A
--SIDT IGN 07/2015
-------------------------------

------
-- for TrafiPollu soft.

SET search_path TO analysis_roundabout_bdtopo, rc_lib, topology, PUBLIC;

WITH edges_selected AS (
    WITH my_roundabouts_points AS (
--trouver les face_ids des centroids
        SELECT DISTINCT
          face_id,
          gid
        FROM test.roundabouts_points
          , topology.GetFaceByPoint('bdtopo_topological', geom, 0) AS face_id
    )
    SELECT
      mr.gid,
      face_id,
      ed.*
    FROM my_roundabouts_points AS mr
      , bdtopo_topological.edge_data AS ed
    WHERE
      ed.left_face = mr.face_id OR ed.right_face = mr.face_id
)
SELECT
  es_gid        AS id,
  ra.geom       AS wkb_centroid   -- geometrie du centre du rond-point,,
  es_list_nodes AS list_nodes     -- list des (id des) nodes (BDTopo) dans le rond-point,,
  es_list_edges AS list_edges -- list des (id des) edges (BDTopo) dans le rond-point
FROM (SELECT
        gid                   AS es_gid,
        array_agg(start_node) AS es_list_nodes,
        array_agg(edge_id)    AS es_list_edges
      FROM edges_selected
      GROUP BY es_gid
     ) AS results_agg
  NATURAL JOIN test.roundabouts_points AS ra
WHERE ra.gid = es_gid