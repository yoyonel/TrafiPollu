__author__ = 'latty'

from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsGeometry

import psycopg2
import psycopg2.extras

import trafipolluImp_DUMP as tpi_DUMP
import imt_tools


class trafipolluImp_SQL(object):
    """

    """

    def __init__(self, iface, dict_edges, dict_lanes, dict_nodes):
        """

        """
        self._map_canvas = iface.mapCanvas()
        #
        self.dict_edges = dict_edges
        self.dict_lanes = dict_lanes
        self.dict_nodes = dict_nodes
        #
        self._dict_sql_methods = {
            'update_table_edges_from_qgis': self._update_tables_from_qgis,
            #
            'dump_informations_from_edges': self._request_for_edges,
            'dump_sides_from_edges': self._request_for_lanes,
            'dump_informations_from_nodes': self._request_for_nodes,
            'dump_informations_from_lane_interconnexion': self._request_for_interconnexions,
        }

        self._dict_params_server = {
            'LOCAL': {
                'host': "localhost",
                'port': "5433",
                'user': "postgres",
                'password': "postgres"
            },
            'IGN': {
                'host': "172.16.3.50",
                'port': "5432",
                'user': "streetgen",
                'password': "streetgen",
            },
        }

        self.connection = None
        self.cursor = None
        self.b_connection_to_postgres_server = False

        self.connect_sql_server()

        # creation de l'objet logger qui va nous servir a ecrire dans les logs
        self.logger = imt_tools.init_logger(__name__)

    def __del__(self):
        """

        :return:
        """
        self.disconnect_sql_server()

    def disconnect_sql_server(self):
        """

        :return:
        """
        if self.b_connection_to_postgres_server:
            self.cursor.close()
            self.connection.close()

    def connect_sql_server(self):
        """

        :return:
        """
        #
        for name_server in self._dict_params_server:
            try:
                self.connection = psycopg2.connect(
                    dbname="street_gen_3",
                    database="bdtopo_topological",
                    **self._dict_params_server[name_server]
                )
            except Exception, e:
                print 'PostGres : problem de connexion -> ', e
            else:
                try:
                    self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
                except Exception, e:
                    print 'PostGres : problem pour recuperer un cursor -> ', e
                else:
                    print 'PostGres: connected with %s server' % name_server
                    self.b_connection_to_postgres_server = True
                    break
        return self.b_connection_to_postgres_server

    def _update_tables_from_qgis(self, *args, **kwargs):
        """

        :param cursor:
        :return:

        """
        try:
            connection = kwargs['connection']
        except:
            pass
        else:
            try:
                self.logger.info("[SQL] - try to commit ...")
                connection.commit()
            except:
                pass

    def build_sql_parameters_with_map_extent(self):
        """

        :return:
        """

        mapCanvas = self._map_canvas
        mapCanvas_extent = mapCanvas.extent()
        # get the list points from the current extent (from QGIS MapCanvas)
        list_points_from_mapcanvas = imt_tools.construct_listpoints_from_extent(mapCanvas_extent)

        # url: http://qgis.org/api/classQgsMapCanvas.html#af0ffae7b5e5ec8b29764773fa6a74d58
        extent_src_crs = mapCanvas.mapSettings().destinationCrs()
        # url: http://qgis.org/api/classQgsCoordinateReferenceSystem.html#a3cb64f24049d50fbacffd1eece5125ee
        extent_postgisSrid = 932011
        extent_dst_crs = QgsCoordinateReferenceSystem(extent_postgisSrid, QgsCoordinateReferenceSystem.PostgisCrsId)
        # url: http://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/crs.html
        xform = QgsCoordinateTransform(extent_src_crs, extent_dst_crs)
        #
        list_points = [xform.transform(point) for point in list_points_from_mapcanvas]

        # list of lists of points
        gPolyline = QgsGeometry.fromPolyline(list_points)
        gPolylineWkt = gPolyline.exportToWkt()

        dict_parameters = {
            'gPolylineWkt': gPolylineWkt,
            'extent_postgisSrid': extent_postgisSrid
        }

        self.logger.info("* list_points_from_mapcanvas: %s", list_points_from_mapcanvas)
        self.logger.info("* gPolygonWkt: %s", gPolylineWkt)
        self.logger.info("* extent_postgisSrid: %s", extent_postgisSrid)
        self.logger.info("extent_src_crs.postgisSrid: %s", extent_src_crs.postgisSrid())

        return dict_parameters

    def execute_sql_commands(self, sql_file, id_sql_method):
        """

        :return:
        """
        if not self.b_connection_to_postgres_server:
            self.connect_sql_server()

        if self.b_connection_to_postgres_server:
            dict_parameters = self.build_sql_parameters_with_map_extent()

            sql_method = self._dict_sql_methods[id_sql_method]

            # all SQL commands (split on ';')
            sqlCommands = sql_file.split(';')

            # Execute every command from the input file
            for command in sqlCommands:
                # This will skip and report errors
                # For example, if the tables do not yet exist, this will skip over
                # the DROP TABLE commands
                try:
                    # command = command.format(gPolylineWkt, extent_postgisSrid)
                    # https://docs.python.org/2/library/string.html#string.Formatter
                    # todo : look here for more advanced features on string formatter
                    # command = command.format(**dict_parameters)

                    if not command.isspace():
                        # url: http://initd.org/psycopg/docs/usage.html#query-parameters
                        # url: http://initd.org/psycopg/docs/advanced.html#adapting-new-types
                        self.cursor.execute(command, dict_parameters)
                        sql_method(connection=self.connection, cursor=self.cursor)
                except psycopg2.OperationalError, msg:
                    self.logger.warning("Command skipped: %s", msg)
                    # #

    def _request_for_edges(self, **kwargs):
        """

        :param kwargs:
        :return:

        """
        try:
            cursor = kwargs['cursor']
        except:
            pass
        else:
            try:
                self.logger.info("[SQL] - try to cursor.fetchall ...")
                objects_from_sql_request = cursor.fetchall()
            except:
                pass
            else:
                self.dict_edges.update(tpi_DUMP.dump_for_edges(objects_from_sql_request))

    def _request_for_nodes(self, **kwargs):
        """

        :param kwargs:
        :return:
        """
        try:
            cursor = kwargs['cursor']
        except:
            pass
        else:
            try:
                self.logger.info("[SQL] - try to cursor.fetchall ...")
                objects_from_sql_request = cursor.fetchall()
            except:
                pass
            else:
                self.dict_nodes.update(tpi_DUMP.dump_for_nodes(objects_from_sql_request))

    def _request_for_interconnexions(self, **kwargs):
        """

        :param kwargs:
        :return:
        """
        try:
            cursor = kwargs['cursor']
        except:
            pass
        else:
            try:
                self.logger.info("[SQL] - try to cursor.fetchall ...")
                objects_from_sql_request = cursor.fetchall()
            except:
                pass
            else:
                # ajouter les informations d'interconnexions au noeud
                (dict_interconnexions, dict_set_id_edges) = tpi_DUMP.dump_for_interconnexions(objects_from_sql_request)
                for node_id, interconnexions in dict_interconnexions.iteritems():
                    self.dict_nodes[node_id].update(
                        {
                            'interconnexions': interconnexions,
                            'set_id_edges': dict_set_id_edges[node_id]
                        }
                    )

    def _request_for_lanes(self, **kwargs):
        """

        :param objects_from_sql_request:
        :param b_load_geom:
        :return:
        """
        try:
            cursor = kwargs['cursor']
        except:
            pass
        else:
            try:
                self.logger.info("[SQL] - try to cursor.fetchall ...")
                objects_from_sql_request = cursor.fetchall()
            except:
                pass
            else:
                tpi_DUMP.dump_lanes(objects_from_sql_request, self.dict_edges, self.dict_lanes)