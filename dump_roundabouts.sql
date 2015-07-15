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
      ed.*
    FROM my_roundabouts_points AS mr
      , bdtopo_topological.edge_data AS ed
    WHERE
      ed.left_face = mr.face_id OR ed.right_face = mr.face_id
)
SELECT
-- test! Demander a Remi une version plus stable/PostGis orientee !
  St_Azimuth(ST_Line_Interpolate_Point(edges_selected.geom, 0.5), node.geom) AS Azimuth,
  edges_selected.*
FROM edges_selected, bdtopo_topological.node AS node
WHERE node.node_id = edges_selected.start_node
ORDER BY gid, Azimuth;
