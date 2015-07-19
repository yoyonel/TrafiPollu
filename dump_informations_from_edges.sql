-------------------------------
--Lionel-A
--SIDT IGN 04/2015
-------------------------------

------
-- for TrafiPollu soft.
-- retrieve (dump) 'informations' from edges selected in QGIS client

SELECT
--
  DISTINCT
  e_s.edge_id,
  axis.lane_number AS axis_lane_number,
  lane.lane_side,
  lane.lane_position,
  lane.lane_direction,
  lane.lane_ordinality,
  ST_AsEWKB(
      CASE lane.lane_direction
      WHEN TRUE THEN lane.lane_center_axis
      ELSE ST_Reverse(lane.lane_center_axis)
      END
  )                AS wkb_lane_center_axis
FROM test.edges_selected AS e_s
  INNER JOIN street_amp.visu_result_lane AS lane ON e_s.edge_id = lane.edge_id
  INNER JOIN street_amp.visu_result_axis AS axis ON e_s.edge_id = axis.edge_id
ORDER BY e_s.edge_id
