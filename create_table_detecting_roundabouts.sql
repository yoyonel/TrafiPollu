-------------------------------
--Lionel-A
--SIDT IGN 07/2015
-------------------------------

------
-- for TrafiPollu soft.
-- add a table


SET search_path TO analysis_roundabout_bdtopo, rc_lib, PUBLIC;

-- url: http://www.tutorialspoint.com/sql/sql-insert-query.htm

--creating the minimal tracking table, other column can be added at will
TRUNCATE TABLE test.roundabouts_points;
CREATE TABLE IF NOT EXISTS test.roundabouts_points (
    gid  SERIAL PRIMARY KEY --mandatory
  , geom geometry (POINT, 932011)
);
--creating index is not mandatory but will speed up all usual operations on those columns
CREATE INDEX ON test.roundabouts_points USING GIST (geom);