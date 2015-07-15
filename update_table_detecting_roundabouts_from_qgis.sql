-------------------------------
--Lionel-A
--SIDT IGN 07/2015
-------------------------------

------
-- for TrafiPollu soft.

INSERT INTO test.roundabouts_points
  SELECT
    row_number()
    OVER () AS gid,
    potential_roundabout
  FROM (
         SELECT
           cluster_label    AS cid,
           cluster_centroid AS potential_roundabout
         FROM street_amp.def_zone_test AS dzt,
           rc_find_roundabout_by_clustering_hough(
               area_of_interest := ST_Transform(
                   ST_GeomFromText(%(gPolylineWkt)s, %(extent_postgisSrid)s),
                   Find_SRID('street_amp', 'def_zone_test', 'geom')
               )
               , max_arc_radius := 80
               , max_dist_in_cluster := 40
               , min_sample_per_cluster := 4)
         UNION ALL
         SELECT
           *
         FROM rc_find_roundabout_by_toponym_analysis(
             area_of_interest := ST_Transform(
                 ST_GeomFromText(%(gPolylineWkt)s, %(extent_postgisSrid)s),
                 Find_SRID('street_amp', 'def_zone_test', 'geom')
             )
             , min_percent_of_place := 0.4
             , threshold_looking_like_a_circle := 0.4)
       ) AS sub;
