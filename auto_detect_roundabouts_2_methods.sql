----------------------
-- Rémi Cura
--2015 Yhales / IGN
--
-- the aim is to try to detect roundabout in bdtopo.road layer
-- we do so by first using hough transform, then clustering
-- necessitate plpythonu, and rc_lib
-----------------------


CREATE SCHEMA IF NOT EXISTS analysis_roundabout_bdtopo;

SET search_path to analysis_roundabout_bdtopo, rc_lib, public;

-----
--example to use : 
-----
SELECT row_number() over() AS gid, potential_roundabout
FROM (
	SELECT cluster_label AS cid , cluster_centroid AS potential_roundabout
	FROM rc_find_roundabout_by_clustering_hough(area_of_interest:=NULL, max_arc_radius:=80  ,max_dist_in_cluster:=40 , min_sample_per_cluster:=4) 
	UNION ALL
	SELECT *
	FROM rc_find_roundabout_by_toponym_analysis(area_of_interest:=NULL,  min_percent_of_place:=0.4, threshold_looking_like_a_circle:=0.4 )   
) AS sub; 






--getting all possible circle centers, allong with radius, from each 3 succesiv poiints of bdtopo.
DROP FUNCTION IF EXISTS rc_array_some_have_pl(iarray anyarray, min_place_threshold float,OUT result boolean  );
CREATE OR REPLACE FUNCTION rc_array_some_have_pl(iarray anyarray, min_place_threshold float DEFAULT 0.5, OUT result boolean  )
 AS 
$BODY$
 --given an array, return true if all values of the array are equal
		DECLARE    
		BEGIN  
			SELECT on_place/array_length(iarray,1) > min_place_threshold INTO result
			FROM (
				SELECT count(*) as on_place 
				FROM unnest(iarray) AS nr
				WHERE nr ILIKE 'PL%' OR nr ILIKE 'NR%'
			) AS sub ; 
			 
		RETURN; 
		END ;  
		$BODY$
  LANGUAGE plpgsql IMMUTABLE STRICT;

DROP FUNCTION IF EXISTS rc_DetectPossibleCircle(igeom geometry, _precision_center FLOAT ,max_radius DOUBLE PRECISION );
CREATE OR REPLACE FUNCTION rc_DetectPossibleCircle(igeom geometry, _precision_center FLOAT , max_radius DOUBLE PRECISION DEFAULT 2147483646 )
RETURNS TABLE(arc_center_x float, arc_center_y float, arc_radius float) AS
$BODY$


--NOTE : replace by appropriate plr or c function (or python) 
		-- @param : the input geometry:  a line where we want to detect the curves
		-- @param :  we deal with non exact computing, the tolerance is then usefull .Expressed in unit of map
		-- @param :  minimal number of points suporting a circle to consider it an arc, default to 3
		--@return : a table : one column with multipoint supporting the arc, the other column with arc center, , the other column with arc radius,, , the other column with number of poitns supporting this arc
		DECLARE   
			_q TEXT;
			_max_int float := 2147483647; 
		BEGIN 

		RETURN QUERY 
			WITH the_geom AS (
					SELECT igeom AS geom ,CASE WHEN _precision_center>0 THEN _precision_center ELSE 0.00001 END AS precision_center
					
				  )
				  ,the_dmp AS ( --dumping the points , preserving the order into path
					SELECT -- the_geom.geom AS total_geom,
						dmp.* 
					--,ST_AsText(dmp.geom)
					FROM the_geom,ST_DumpPoints(geom) AS dmp
					)
					,geom_array AS ( --simply an array of all the point ordered according to path. 
						--non optimal, but make it simpler to write the last part
						SELECT array_agg(geom ORDER BY path ASC) AS geom_a
							
						FROM the_dmp
					)
					,hough_t AS ( --for each triplet of point, find what kind of circle passes trough all 3 points
						SELECT path, td.geom
							,ST_Astext(ST_Collect(ARRAY[td.geom,lead(td.geom,1) OVER(),lead(td.geom,2) OVER() ]) )
							, rc_lib.rc_circular_hough_transform (ST_Collect(ARRAY[td.geom,lead(td.geom,1) OVER(),lead(td.geom,2) OVER() ])   ,tg.precision_center)as c 
						FROM the_dmp As td, the_geom as tg
					)
					,proper_hough AS (
						SELECT path, h.geom , (c).center AS c,(c).radius as radius 
						FROM hough_t AS h, the_geom AS tg
						WHERE (c).radius IS NOT NULL AND (c).radius < max_radius AND (c).radius >0 AND (c).radius / tg.precision_center <_max_int
					)
					--,rounded AS (--rounding the detected radius of circle acording to user defined parameter
					SELECT  ST_X(c) AS cx , ST_Y(c) AS cy 
						, CASE WHEN precision_center   <= 0 THEN  radius ELSE (radius/tg.precision_center)::int*tg.precision_center END AS cr
						--,st_astext(c)
					FROM proper_hough AS ph, the_geom AS tg ;

					RETURN; 
		END ;
			 
		$BODY$
  LANGUAGE plpgsql IMMUTABLE STRICT;


--first approach  : finding parts of the road network that look like a circle

DROP FUNCTION IF EXISTS rc_find_roundabout_by_clustering_hough(area_of_interest geometry, max_arc_radius float,max_dist_in_cluster float, min_sample_per_cluster int   );
CREATE OR REPLACE FUNCTION rc_find_roundabout_by_clustering_hough(area_of_interest geometry, max_arc_radius float DEFAULT 80, max_dist_in_cluster float DEFAULT 40, min_sample_per_cluster int default 4   )   
RETURNS TABLE (cluster_label int,cluster_centroid geometry(point,932011)) AS 
$BODY$
		 /** @brief decomposate road geom in the given area into successive 3 points, then Hough transform, then cluster to find probable roundabouts
			First every line in road network is decomposated into triplet of successive points. 
				Then we perform a Hough transform (estimate the radius and center of a circle passing by the tripplet).
				Then we use the DBSCAN algorithm to cluster the potential circle by the position of thir center (_not_ radius).
				The dbscan algo is controlled by the classical 2 parameters : max distance within one cluster, and minimum member number of a cluster
			@param area_of_interest : only look for roundabouts int his area. Put it to null to look everywhere
			@param max_arc_radius : maximum allowed raidus of of potential arc of circle, in meter
			@param max_dist_in_cluster : a cluster of potential cirlce center should not have centers farther than this
			@param min_sample_per_cluster : a cluster of potential circle center should not have less than this number of circle centers. 
		 */
		DECLARE    
		BEGIN 
		RETURN QUERY 
		WITH circle_detection AS (	
			SELECT gid,row_number() over() as uid
				, id
				, f.* 
				, ST_SetSRID(ST_MakePoint(arc_center_x, arc_center_y ),932011)::geometry(point,932011) AS circle_center_candidate
			FROM bdtopo.road as r, rc_DetectPossibleCircle (ST_Transform(r.geom,932011)
									, _precision_center := 0	, max_radius := max_arc_radius ) as f 
			WHERE ST_Intersects(r.geom, area_of_interest) = TRUE OR area_of_interest IS NULL  
		)
		, agg_data AS (
			SELECT array_agg(uid::int ORDER BY uid) as gids 
				--,array_agg_custom(ARRAY[arc_center_x,arc_center_y, arc_radius] ORDER BY uid) as dat
				,array_agg_custom(ARRAY[arc_center_x,arc_center_y] ORDER BY uid) as dat
			FROM circle_detection AS cd   
		)
		, clustering AS (
			SELECT r.*
			FROM agg_data AS cd
				--, rc_py_cluster_points_dbscan( gids, dat, 3,  max_dist := 20, min_sample := 4 ) AS r 
				, rc_py_cluster_points_dbscan( gids, dat, 2,  max_dist := max_dist_in_cluster, min_sample := min_sample_per_cluster ) AS r 
		)
		, circle_clustering AS (
			SELECT cc.uid,label, circle_center_candidate 
			FROM clustering AS c
				LEFT OUTER JOIN circle_detection AS cc ON (c.gid = cc.uid) 
		 )
		 SELECT cc.label::int 
			, ST_Centroid(ST_Collect(circle_center_candidate))::geometry(point,932011) as cluster_centroid
		FROM circle_clustering  AS cc 
		GROUP BY label ; 

		RETURN; 
		END ;  
		$BODY$
  LANGUAGE plpgsql VOLATILE CALLED ON NULL INPUT;

SELECT *
FROM rc_find_roundabout_by_clustering_hough(NULL, max_arc_radius:=80  ,max_dist_in_cluster:=40 , min_sample_per_cluster:=4) ; 


/*
  

DROP TABLE IF EXISTS circle_detection ;
CREATE TABLE circle_detection  AS
  SELECT gid,row_number() over() as uid, id, f.* , ST_SetSRID(ST_MakePoint(arc_center_x, arc_center_y ),932011)::geometry(point,932011) AS circle_center_candidate
  FROM bdtopo.road as r, rc_DetectPossibleCircle (ST_Transform(r.geom,932011)
		, _precision_center := 0		, max_radius := 80 ) as f ;  
 


--clustering the circle detection
--we use plpython, scipy and dbscan for unsupervised clustering
-- we cluster on x,y

DROP TABLE IF EXISTS circle_clustering ;
CREATE TABLE circle_clustering AS 
		WITH agg_data AS (
			SELECT array_agg(uid::int ORDER BY uid) as gids 
				,array_agg_custom(ARRAY[arc_center_x,arc_center_y, arc_radius] ORDER BY uid) as dat
			FROM circle_detection AS cd   
		)
		, clustering AS (
			SELECT r.*
			FROM agg_data AS cd
				, rc_py_cluster_points_dbscan( gids, dat, 3,  max_dist := 20, min_sample := 4 ) AS r 
		)
		SELECT cc.uid,label, circle_center_candidate 
		FROM clustering AS c
			LEFT OUTER JOIN circle_detection AS cc ON (c.gid = cc.uid) ;



	DROP TABLE IF EXISTS visu_cluster ;
	CREATE TABLE visu_cluster AS 

	SELECT cc.label , ST_Centroid(ST_Collect(circle_center_candidate))::geometry(point,932011) as cluster_centroid
	FROM circle_clustering  AS cc 
	GROUP BY label ; 

*/

-- second approach, taking all faces of the road network using topology, keeping those where all the roads have the same name, or contains 'place'
--, and look a little bit like a circle


DROP FUNCTION IF EXISTS rc_find_roundabout_by_toponym_analysis(area_of_interest geometry,min_percent_of_place float , threshold_looking_like_a_circle float      );
CREATE OR REPLACE FUNCTION rc_find_roundabout_by_toponym_analysis(area_of_interest geometry,  min_percent_of_place float default 0.4, threshold_looking_like_a_circle float default 0.4 )   
RETURNS TABLE (face_id int,face_centroid geometry(point,932011)) AS 
$BODY$
		 /** @brief  get all the edges street name, then group into faces. Then keep faces which streets have the same name, or that contains a given % of 'place' name. Keep faces looking a little bit like a circle
			@param area_of_interest : only look for roundabouts int his area. Put it to null to look everywhere
			@param min_percent_of_place : given all the edges of a face, min_percent_of_place% of this edges should be name 'place...'
			@param threshold_looking_like_a_circle : for potential faces ,we test if are(face)/area(containing_circle(face))> threshold_looking_like_a_circle. Put it to null to not use any geometrical criteria
		 */
		DECLARE    
		BEGIN 
		RETURN QUERY 
			WITH edge_ids AS (
				SELECT edge_id, left_face as face_id, LEAST(nom_rue_g, nom_rue_d) as nrue 
				FROM bdtopo_topological.edge_data AS ed
					LEFT OUTER JOIN bdtopo.road AS r ON (r.id = ed.ign_id) 
				WHERE left_face !=0 AND (ST_INtersects(area_of_interest,ed.geom)OR  area_of_interest IS  NULL ) 
				UNION ALL 
				SELECT edge_id, right_face as face_id, LEAST(nom_rue_g, nom_rue_d) as nrue
				FROM bdtopo_topological.edge_data AS ed
					LEFT OUTER JOIN bdtopo.road AS r ON (r.id = ed.ign_id) 
				WHERE right_face !=0 AND  (ST_INtersects(area_of_interest,ed.geom) OR   area_of_interest IS NULL)
			)
			, candidates AS (
				SELECT ei.face_id,  array_agg(edge_id) as edge_ids, array_agg(nrue) AS nrues 
				FROM edge_ids AS ei
				GROUP BY ei.face_id 
			)
			,results  AS(
				SELECT c.face_id, nrues[1] AS nrues, topology.ST_GetFaceGeometry('bdtopo_topological', c.face_id)::geometry(polygonZ,932011)  as face_geom 
				FROM candidates AS c
				WHERE ( rc_array_AllSameValue(nrues) = True
					OR  rc_array_some_have_pl(nrues,min_place_threshold:= min_percent_of_place) = True
					) AND c.face_id != 0 --security
			)
			SELECT r.face_id, ST_Force2D(ST_Centroid(face_geom))::geometry(POINT,932011)  
			FROM results AS r
			WHERE 
				ST_Area(face_geom)/ST_Area(ST_MinimumBoundingCircle(face_geom))>threshold_looking_like_a_circle OR threshold_looking_like_a_circle IS NULL;

		RETURN; 
		END ;  
		$BODY$
  LANGUAGE plpgsql VOLATILE CALLED ON NULL INPUT;

SELECT *
FROM rc_find_roundabout_by_toponym_analysis(area_of_interest:=NULL,  min_percent_of_place:=0.4, threshold_looking_like_a_circle:=0.4 )   
 


/*
-- second approach, using topoloyg
-- getting all faces, keeping only faces having all the same street name

--grouping the road by those having the same name, checking that they have a common left_fact, right_face

DROP TABLE IF EXISTS possible_roundabouts_from_topo ; 
CREATE TABLE possible_roundabouts_from_topo AS 
	WITH edge_ids AS (
		SELECT edge_id, left_face as face_id, LEAST(nom_rue_g, nom_rue_d) as nrue
		FROM bdtopo_topological.edge_data AS ed
			LEFT OUTER JOIN bdtopo.road AS r ON (r.id = ed.ign_id) 
		UNION ALL 
		SELECT edge_id, right_face as face_id, LEAST(nom_rue_g, nom_rue_d) as nrue
		FROM bdtopo_topological.edge_data AS ed
			LEFT OUTER JOIN bdtopo.road AS r ON (r.id = ed.ign_id) 
	)
	, candidates AS (
	SELECT face_id,  array_agg(edge_id) as edge_ids, array_agg(nrue) AS nrues 
	FROM edge_ids
	GROUP BY face_id 
	)
	,results  AS(
	SELECT face_id, nrues[1] AS nrues, topology.ST_GetFaceGeometry('bdtopo_topological', face_id)::geometry(polygonZ,932011)  as face_geom 
	FROM candidates
	WHERE ( rc_array_AllSameValue(nrues) = True
		OR  rc_array_some_have_pl(nrues,min_place_threshold:= 0.5) = True
		) AND face_id != 0
	)
	SELECT *
	FROM results
	WHERE --st_area(ST_Envelope( face_geom)) < 5000 
		 ST_Area(face_geom)/ST_Area(ST_MinimumBoundingCircle(face_geom))>0.65;


SELECT *
FROM  bdtopo.road 
LIMIT 10; 

*/
