__author__ = 'latty'

from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsGeometry
import psycopg2
import psycopg2.extras

import trafipolluImp_DUMP as tpi_DUMP
import imt_tools
import trafipolluImp_Tools_Symuvia as tpi_TS

class trafipolluImp_SQL(object):
    """

    """

    # def __init__(self, iface, dict_edges, dict_lanes, dict_nodes):
    def __init__(self, **kwargs):
        """

        """
        self.dict_edges = kwargs['dict_edges']
        self.dict_nodes = kwargs['dict_nodes']
        self.dict_lanes = kwargs['dict_lanes']

        iface = kwargs['iface']
        self._map_canvas = iface.mapCanvas()
        #
        self._dict_sql_methods = {
            'update_def_zone_test': self._update_tables_from_qgis,
            'update_table_edges_from_qgis': self._update_tables_from_qgis,
            'update_tables_from_def_zone_test': self._update_tables_from_qgis,
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
                'password': "postgres",
                'connect_timeout': 2,
            },
            'IGN': {
                'host': "172.16.3.50",
                'port': "5432",
                'user': "streetgen",
                'password': "streetgen",
                'connect_timeout': 2,
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
        # srid of translated lambert 93 to match laser referential
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

    @staticmethod
    def build_sql_parameters_with_update_def_zone_test(
            b_update_def_zone_test_with_convex_hull_on_symuvia_network=False,
            **kwargs
    ):
        """

        :return:

        """

        gPolygonWkt = ''

        if b_update_def_zone_test_with_convex_hull_on_symuvia_network:
            convex_hull, list_extremites = tpi_TS.extract_convexhull_from_symuvia_network(**kwargs)
            gPolygonWkt = convex_hull.wkt

        if gPolygonWkt == '':
            # Convex hull du reseau symuvia '/home/latty/__DEV__/__Ifsttar__/Envoi_IGN_2015_07/reseau_paris6_v31.xml'
            gPolygonWkt = 'POLYGON ((650701.858831 6860988.892569, 650685.579302 6860989.63957, 650637.589042 6861000.671025, 650625.9989689999 6861022.21112, 650475.062469 6861507.425974, 650919.609638 6862039.011138, 650988.736866 6862060.741522, 651337.303769 6861890.548595, 651383.122202 6861735.047361, 651396.56811 6861476.753853, 651404.1191219999 6861230.871522, 651403.524419 6861226.192165, 651019.06407 6861047.190387, 650836.022246 6861012.096856, 650701.858831 6860988.892569))'

        gPolygonSRID = 2154  # SRID du Lambert93

        print '################ gPolygonWkt: ', gPolygonWkt

        dict_parameters = {
            'gPolygonWkt': gPolygonWkt,
            'gPolygonSRID': gPolygonSRID
        }

        return dict_parameters

    def execute_sql_commands(self, sql_file, id_sql_method):
        """

        :return:
        """
        if not self.b_connection_to_postgres_server:
            self.connect_sql_server()

        if self.b_connection_to_postgres_server:

            dict_parameters = {}
            if id_sql_method == 'update_table_edges_from_qgis':
                dict_parameters = self.build_sql_parameters_with_map_extent()
            elif id_sql_method == 'update_def_zone_test':
                dict_parameters = self.build_sql_parameters_with_update_def_zone_test()

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