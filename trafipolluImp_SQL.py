__author__ = 'latty'

from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsGeometry

import psycopg2
import psycopg2.extras

import trafipolluImp_DUMP as tpi_DUMP
import imt_tools
import trafipolluImp_Tools_Symuvia as tpi_TS
from imt_tools import init_logger

# creation de l'objet logger qui va nous servir a ecrire dans les logs
logger = init_logger(__name__)

import ConfigParser
from collections import defaultdict
from Config_Tools import CConfig

import os


qgis_plugins_directory = os.path.normcase(os.path.dirname(__file__))


class trafipolluImp_SQL(object):
    """

    """

    def __init__(self, **kwargs):
        """

        """
        self.dict_edges = kwargs['dict_edges']
        self.dict_nodes = kwargs['dict_nodes']
        self.dict_lanes = kwargs['dict_lanes']
        self.dict_roundabouts = kwargs['dict_roundabouts']

        iface = kwargs['iface']
        self._map_canvas = iface.mapCanvas()

        #
        self._dict_sql_methods = {
            'update_def_zone_test': self._update_tables_from_qgis,
            'update_table_edges_from_qgis': self._update_tables_from_qgis,
            'update_tables_from_def_zone_test': self._update_tables_from_qgis,
            #
            'update_table_detecting_roundabouts_from_qgis': self._update_tables_from_qgis,
            #
            'dump_informations_from_edges': self._request_for_edges,
            'dump_sides_from_edges': self._request_for_lanes,
            'dump_informations_from_nodes': self._request_for_nodes,
            'dump_informations_from_lane_interconnexion': self._request_for_interconnexions,
            # TODO: travail sur les rond points [desactiver]
            # 'dump_roundabouts': self._request_for_roundabouts
        }

        self.config_filename = qgis_plugins_directory + '/' + \
                               kwargs.setdefault('config_filename', 'config_' + __name__ + '.ini')
        self._dict_params_server = self.get_params_server_from_ini_config(self.config_filename)

        self.connection = None
        self.cursor = None
        self.b_connection_to_postgres_server = False

        self.connect_sql_server()

    def get_params_server_from_ini_config(self, config_filename):
        """

        :return:
        """
        logger.info("Config INI filename: {0}".format(self.config_filename))
        configs = CConfig(config_filename)
        try:
            configs.load()
        except ConfigParser.ParsingError:
            logger.warning("can't read the file: {0}".format(self.config_filename))
            logger.warning("Utilisation des valeurs par defaut (orientees pour une target precise)")

        dict_params_server = defaultdict(dict)

        # load une section du fichier config
        configs.load_section('SQL_LOCAL_SERVER')
        # recuperation des options liees a la section courante 'SQL_LOCAL_SERVER'
        configs.update(
            dict_params_server['LOCAL'],
            {
                'host': ('host', 'localhost'),
                'port': ('port', '5433'),
                'user': ('user', 'postgres'),
                'password': ('password', 'postgres'),
                'connect_timeout': ('connect_timeout', '2'),
                #
                'dbname': ('dbname', 'street_gen_3'),
                'database': ('database', 'bdtopo_topological')
            }
        )

        # load une section du fichier config
        configs.load_section('SQL_IGN_SERVER')
        # recuperation des options liees a la section courante 'SQL_IGN_SERVER'
        configs.update(
            dict_params_server['IGN'],
            {
                'host': ('host', '172.16.3.50'),
                'port': ('port', '5432'),
                'user': ('user', 'streetgen'),
                'password': ('password', 'streetgen'),
                'connect_timeout': ('connect_timeout', '2'),
                #
                'dbname': ('dbname', 'street_gen_4'),
                'database': ('database', 'bdtopo_topological')
            }
        )

        return dict_params_server

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
                self.connection = psycopg2.connect(**self._dict_params_server[name_server])
            except psycopg2.Error as e:
                logger.warning("PsyCopg2 Error : %s - Detail: %s" % (e.pgerror, e.diag.message_detail))
            else:
                try:
                    self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
                except Exception, e:
                    logger.fatal('Probleme pour recuperer un cursor -> %s' % e)
                else:
                    logger.info('connected with %s server' % name_server)
                    logger.info('informations de connections:')
                    map(
                        lambda s: logger.info(s),
                        map(
                            lambda x: '- ' + str(x[0]) + ': ' + str(x[1]),
                            self._dict_params_server[name_server].iteritems()
                        )
                    )
                    self.b_connection_to_postgres_server = True
                    break

        if not self.b_connection_to_postgres_server:
            logger.fatal('Impossible de se connecter a un serveur !')

        return self.b_connection_to_postgres_server

    @staticmethod
    def _update_tables_from_qgis(*args, **kwargs):
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
                logger.info("[SQL] - try to commit ...")
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

        logger.info("* list_points_from_mapcanvas: %s", list_points_from_mapcanvas)
        logger.info("* gPolygonWkt: %s", gPolylineWkt)
        logger.info("* extent_postgisSrid: %s", extent_postgisSrid)
        logger.info("extent_src_crs.postgisSrid: %s", extent_src_crs.postgisSrid())

        return dict_parameters

    def build_sql_parameters_with_map_extent_for_roundabouts(self):
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
        gPolygon = QgsGeometry.fromPolygon([list_points])
        gPolygoneWkt = gPolygon.exportToWkt()

        dict_parameters = {
            'gPolygonWkt': gPolygoneWkt,
            'extent_postgisSrid': extent_postgisSrid
        }

        logger.info("* list_points_from_mapcanvas: %s", list_points_from_mapcanvas)
        logger.info("* gPolygonWkt: %s", gPolygoneWkt)
        logger.info("* extent_postgisSrid: %s", extent_postgisSrid)
        logger.info("extent_src_crs.postgisSrid: %s", extent_src_crs.postgisSrid())

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
            shp_convex_hull, shp_list_extremites = tpi_TS.extract_convexhull_from_symuvia_network(**kwargs)
            gPolygonWkt = shp_convex_hull.wkt

        if gPolygonWkt == '':
            # Convex hull du reseau symuvia '/home/latty/__DEV__/__Ifsttar__/Envoi_IGN_2015_07/reseau_paris6_v31.xml'
            gPolygonWkt = 'POLYGON ((650701.858831 6860988.892569, 650685.579302 6860989.63957, 650637.589042 6861000.671025, 650625.9989689999 6861022.21112, 650475.062469 6861507.425974, 650919.609638 6862039.011138, 650988.736866 6862060.741522, 651337.303769 6861890.548595, 651383.122202 6861735.047361, 651396.56811 6861476.753853, 651404.1191219999 6861230.871522, 651403.524419 6861226.192165, 651019.06407 6861047.190387, 650836.022246 6861012.096856, 650701.858831 6860988.892569))'

        gPolygonSRID = 2154  # SRID du Lambert93

        logger.info('################ gPolygonWkt: ', gPolygonWkt)

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

            dict_parameters = self.build_parameters_for_sql_method(id_sql_method)

            try:
                sql_method = self._dict_sql_methods[id_sql_method]
            except:
                sql_method = None
                logger.warning('Pas de methode (python) associee au script sql: %s' % id_sql_method)

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
                        if sql_method:
                            sql_method(connection=self.connection, cursor=self.cursor)
                except psycopg2.OperationalError, msg:
                    logger.warning("Command skipped: %s", msg)

    def build_parameters_for_sql_method(self, id_sql_method):
        """

        :param id_sql_command:
        :return:
        """
        dict_parameters = {}
        if id_sql_method == 'update_table_edges_from_qgis':
            dict_parameters = self.build_sql_parameters_with_map_extent()
        elif id_sql_method == 'update_table_detecting_roundabouts_from_qgis':
            dict_parameters = self.build_sql_parameters_with_map_extent_for_roundabouts()
        elif id_sql_method == 'update_def_zone_test':
            dict_parameters = self.build_sql_parameters_with_update_def_zone_test()
        return dict_parameters

    def _request_for_roundabouts(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return:

        """
        cursor = kwargs['cursor']
        try:
            logger.info("[SQL] - try to cursor.fetchall ...")
            objects_from_sql_request = cursor.fetchall()
        except Exception, e:
            logger.warning("[SQL] Exception: %s" % e)
        else:
            self._post_request_for_roundabouts(tpi_DUMP.dump_for_roundabouts(objects_from_sql_request))

    def _post_request_for_roundabouts(self, results_dump):
        """

        :param results_dump:
        :return:
        """
        dict_roundabouts = results_dump

        for ra_id, ra_dump in dict_roundabouts.iteritems():
            # ajouter les informations aux 'nodes'
            for node_id in ra_dump['list_nodes']:
                if node_id in self.dict_nodes:
                    self.dict_nodes[node_id].update({'roundabouts': ra_id})
            # ajouter les informations aux 'edges'
            for edge_id in ra_dump['list_edges']:
                if edge_id in self.dict_edges:
                    self.dict_edges[edge_id].update({'roundabouts': ra_id})

        self.dict_roundabouts.update(dict_roundabouts)

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
                logger.info("[SQL] - try to cursor.fetchall ...")
                objects_from_sql_request = cursor.fetchall()
            except Exception, e:
                logger.warning("[SQL] Exception: %s" % e)
            else:
                self._post_request_for_edges(tpi_DUMP.dump_for_edges(objects_from_sql_request))

    def _post_request_for_edges(self, results_dump):
        """

        :param results_dump:
        :return:
        """
        dict_edges = results_dump
        self.dict_edges.update(dict_edges)

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
                logger.info("[SQL] - try to cursor.fetchall ...")
                objects_from_sql_request = cursor.fetchall()
            except Exception, e:
                logger.warning("[SQL] Exception: %s" % e)
            else:
                self._post_request_for_nodes(tpi_DUMP.dump_for_nodes(objects_from_sql_request))

    def _post_request_for_nodes(self, results_dump):
        """

        :param results_dump:
        :return:
        """
        dict_nodes = results_dump
        self.dict_nodes.update(dict_nodes)

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
                logger.info("[SQL] - try to cursor.fetchall ...")
                objects_from_sql_request = cursor.fetchall()
            except Exception, e:
                logger.warning("[SQL] Exception: %s" % e)
            else:
                self._post_request_for_interconnexions(tpi_DUMP.dump_for_interconnexions(objects_from_sql_request))

    def _post_request_for_interconnexions(self, results_dump):
        """

        :param results_dump:
        :return:
        """
        dict_interconnexions, dict_set_id_edges = results_dump

        # ajouter les informations d'interconnexions au noeud
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
                logger.info("[SQL] - try to cursor.fetchall ...")
                objects_from_sql_request = cursor.fetchall()
            except Exception, e:
                logger.warning("[SQL] Exception: %s" % e)
            else:
                self._post_request_for_lanes(tpi_DUMP.dump_lanes(objects_from_sql_request, self.dict_edges))

    def _post_request_for_lanes(self, results_dump):
        """

        :param results_dump:
        :return:
        """
        dict_lanes, dict_grouped_lanes = results_dump

        self.dict_lanes.update(dict_lanes)
        # update dict_edges with lanes grouped informations
        for sg3_edge_id, grouped_lanes in dict_grouped_lanes.items():
            self.dict_edges[sg3_edge_id].update(grouped_lanes)